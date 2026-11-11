`timescale 1ns/1ps

// On-chip block-RAM memory with the daq_top command/response interface.
// It stands in for external DDR on the board build. It has one response
// register, so it holds at most one command; the response arrives one cycle
// after the command is accepted. Misaligned or out-of-range addresses return
// rsp_error without touching storage.
module bram_memory #(
    parameter int MEM_BYTES = 4096
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        cmd_valid,
    output logic        cmd_ready,
    input  logic        cmd_write,
    input  logic [31:0] cmd_addr,
    input  logic [63:0] cmd_data,
    output logic        rsp_valid,
    output logic        rsp_error,
    output logic [63:0] rsp_data,
    input  logic        rsp_ready
);
    localparam int WORDS  = MEM_BYTES / 8;
    localparam int ADDR_W = $clog2(WORDS);

    logic [63:0] storage [0:WORDS-1];
    logic [ADDR_W-1:0] index;
    logic accept, in_range;

    assign index     = cmd_addr[ADDR_W+2:3];
    assign in_range  = (cmd_addr[2:0] == 3'b0) && ({1'b0, cmd_addr} + 33'd8 <= 33'(MEM_BYTES));
    assign cmd_ready = !rsp_valid;
    assign accept    = cmd_valid && cmd_ready;

    // Kept free of reset so synthesis maps it onto block RAM.
    always_ff @(posedge clk) begin
        if (accept && in_range) begin
            if (cmd_write) storage[index] <= cmd_data;
            else           rsp_data       <= storage[index];
        end
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            rsp_valid <= 1'b0;
            rsp_error <= 1'b0;
        end else if (accept) begin
            rsp_valid <= 1'b1;
            rsp_error <= !in_range;
        end else if (rsp_ready) begin
            rsp_valid <= 1'b0;
        end
    end
`ifndef SYNTHESIS
    initial begin
        if (MEM_BYTES < 16 || MEM_BYTES % 8 != 0 || (MEM_BYTES & (MEM_BYTES - 1)) != 0)
            $fatal(1, "MEM_BYTES must be a power of two, at least 16");
    end
    assert property (@(posedge clk) disable iff (!rst_n)
        rsp_valid && !rsp_ready |=> rsp_valid && $stable({rsp_error, rsp_data}));
`endif
endmodule
