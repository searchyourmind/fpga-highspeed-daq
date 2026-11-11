`timescale 1ns/1ps

// ULX3S board top for the DAQ core (Lattice LFE5U-25F, 25 MHz oscillator).
//
// The PC sends descriptors over the FTDI UART and the board streams every link
// beat and every completion back. Every daq_top input comes from received
// bytes, so synthesis cannot constant-fold the descriptor validation, address
// or packetizer logic; the resource and timing numbers describe the real core.
// External DDR is replaced by on-chip block RAM (bram_memory).
//
// Host -> FPGA: 0x5A, then 22 bytes, multi-byte fields little-endian:
//   id[16] start[16] length[16] base[32] host[64] owner[8] frame_len[16] gain[8]
// FPGA -> host, one per link beat (9 bytes):
//   0xD0 | {last, eop, sop}, data[64]
// FPGA -> host, one per completion (10 bytes):
//   0xC0, id[16], status[8], beats[16], checksum[32]
// checksum = per beat, rotate left by 1 then add (mod 2^32)
//   data[31:0] ^ data[63:32] ^ addr[31:0] ^ addr[63:32] ^ {tag, length} ^ {last, eop, sop}
// so the host can check addresses, tags and lengths it does not receive directly.
module fpga_top #(
    parameter int CLKS_PER_BIT = 217,  // 25 MHz / 115200 baud
    parameter int RING_WORDS = 32, MEM_BYTES = 4096, FIFO_DEPTH = 8, MAX_WORDS = 4
) (
    input  logic       clk_25mhz,
    input  logic       btn_fire1,  // active-high reset request
    input  logic       ftdi_txd,   // UART, PC to FPGA
    output logic       ftdi_rxd,   // UART, FPGA to PC
    output logic [7:0] led
);
    localparam int CMD_BYTES = 22;

    logic clk;
    assign clk = clk_25mhz;

    // Power-on and button reset: held for 15 cycles, released synchronously.
    // These flops have no reset of their own; the bitstream loads their
    // initial values at configuration, which is what PROCASSINIT flags.
    /* verilator lint_off PROCASSINIT */
    logic       btn_meta = 1'b0, btn_sync = 1'b0;
    logic [3:0] por_count = 4'd0;
    logic       rst_n = 1'b0;
    /* verilator lint_on PROCASSINIT */
    always_ff @(posedge clk) begin
        btn_meta <= btn_fire1;
        btn_sync <= btn_meta;
        if (btn_sync) por_count <= '0;
        else if (por_count != 4'hf) por_count <= por_count + 1'b1;
        rst_n <= (por_count == 4'hf);
    end

    // Descriptor command parser.
    logic [7:0] rx_data;
    logic       rx_valid;
    logic [8*CMD_BYTES-1:0] cmd;
    logic [4:0] cmd_count;
    logic       in_frame, desc_valid, desc_ready;

    uart_rx #(.CLKS_PER_BIT(CLKS_PER_BIT)) rx_i (
        .clk, .rst_n, .rx(ftdi_txd), .data(rx_data), .valid(rx_valid));

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            cmd        <= '0;
            cmd_count  <= '0;
            in_frame   <= 1'b0;
            desc_valid <= 1'b0;
        end else begin
            if (desc_valid && desc_ready) desc_valid <= 1'b0;
            // Bytes that arrive while a descriptor waits are dropped.
            if (rx_valid && !desc_valid) begin
                if (!in_frame) begin
                    if (rx_data == 8'h5A) begin
                        in_frame  <= 1'b1;
                        cmd_count <= '0;
                    end
                end else begin
                    cmd       <= {rx_data, cmd[8*CMD_BYTES-1:8]};
                    cmd_count <= cmd_count + 1'b1;
                    if (cmd_count == 5'(CMD_BYTES-1)) begin
                        in_frame   <= 1'b0;
                        desc_valid <= 1'b1;
                    end
                end
            end
        end
    end

    // DAQ core.
    logic        comp_valid, comp_ready;
    logic [15:0] comp_id;
    logic [2:0]  comp_status;
    logic        mem_cmd_valid, mem_cmd_write, mem_cmd_ready;
    logic [31:0] mem_cmd_addr;
    logic [63:0] mem_cmd_data, mem_rsp_data;
    logic        mem_rsp_valid, mem_rsp_error, mem_rsp_ready;
    logic [63:0] link_data, link_addr;
    logic [15:0] link_tag, link_length;
    logic        link_valid, link_sop, link_eop, link_last, link_ready;
    logic [$clog2(FIFO_DEPTH+1)-1:0] fifo_occupancy;

    daq_top #(.RING_WORDS(RING_WORDS), .MEM_BYTES(MEM_BYTES), .FIFO_DEPTH(FIFO_DEPTH),
              .MAX_WORDS(MAX_WORDS)) daq_i (
        .clk, .rst_n,
        .desc_valid, .desc_ready,
        .desc_id(cmd[15:0]), .desc_start(cmd[31:16]), .desc_length(cmd[47:32]),
        .desc_base(cmd[79:48]), .desc_host(cmd[143:80]), .desc_owner(cmd[144]),
        .frame_len(cmd[167:152]), .gain(cmd[175:168]),
        .comp_valid, .comp_ready, .comp_id, .comp_status,
        .mem_cmd_valid, .mem_cmd_write, .mem_cmd_ready, .mem_cmd_addr, .mem_cmd_data,
        .mem_rsp_valid, .mem_rsp_error, .mem_rsp_data, .mem_rsp_ready,
        .link_data, .link_addr, .link_tag, .link_length,
        .link_valid, .link_sop, .link_eop, .link_last, .link_ready,
        .fifo_occupancy);

    bram_memory #(.MEM_BYTES(MEM_BYTES)) memory_i (
        .clk, .rst_n,
        .cmd_valid(mem_cmd_valid), .cmd_ready(mem_cmd_ready), .cmd_write(mem_cmd_write),
        .cmd_addr(mem_cmd_addr), .cmd_data(mem_cmd_data),
        .rsp_valid(mem_rsp_valid), .rsp_error(mem_rsp_error), .rsp_data(mem_rsp_data),
        .rsp_ready(mem_rsp_ready));

    // Report serializer: one message at a time, sent least-significant byte first.
    // The UART is the bottleneck, so link_ready also exercises core backpressure.
    logic [79:0] msg;
    logic [3:0]  msg_bytes;
    logic [15:0] beat_count;
    logic [31:0] checksum, fold;
    logic [4:0]  jobs_done;
    logic        error_seen, tx_ready;

    assign link_ready = (msg_bytes == 0);
    assign comp_ready = (msg_bytes == 0) && !link_valid;
    assign fold = link_data[31:0] ^ link_data[63:32] ^ link_addr[31:0] ^ link_addr[63:32]
                ^ {link_tag, link_length} ^ {29'b0, link_last, link_eop, link_sop};

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            msg        <= '0;
            msg_bytes  <= '0;
            beat_count <= '0;
            checksum   <= '0;
            jobs_done  <= '0;
            error_seen <= 1'b0;
        end else if (msg_bytes != 0) begin
            if (tx_ready) begin
                msg       <= msg >> 8;
                msg_bytes <= msg_bytes - 1'b1;
            end
        end else if (link_valid) begin
            msg        <= {8'h00, link_data, 5'b11010, link_last, link_eop, link_sop};
            msg_bytes  <= 4'd9;
            beat_count <= beat_count + 1'b1;
            checksum   <= {checksum[30:0], checksum[31]} + fold;
        end else if (comp_valid) begin
            msg        <= {checksum, beat_count, 5'b0, comp_status, comp_id, 8'hC0};
            msg_bytes  <= 4'd10;
            beat_count <= '0;
            checksum   <= '0;
            jobs_done  <= jobs_done + 1'b1;
            if (comp_status != 0) error_seen <= 1'b1;
        end
    end

    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) tx_i (
        .clk, .rst_n, .s_data(msg[7:0]), .s_valid(msg_bytes != 0), .s_ready(tx_ready),
        .tx(ftdi_rxd));

    assign led = {jobs_done, error_seen, link_valid, !desc_ready};

    logic unused_ok;
    assign unused_ok = &{1'b0, cmd[151:145], fifo_occupancy};
endmodule
