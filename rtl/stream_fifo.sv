`timescale 1ns/1ps

// Implemented from the supplied Week 1 starter; arbitrary positive depth.
// This is a register-array FIFO, NOT a DDR memory controller or PCIe endpoint.
//
// Contract:
//  * A transfer at input happens ONLY when s_valid && s_ready at rising clk.
//  * A transfer at output happens ONLY when m_valid && m_ready at rising clk.
//  * When m_valid && !m_ready, m_data and m_valid must remain stable.
//  * reset clears occupancy and pending output (contents need not be cleared).
//  * Simultaneous accepted read/write preserves occupancy.
//  * Simplicity: no fall-through on empty; when full, reject pushes even if a pop
//    is accepted on the same cycle (legal, but not peak-throughput optimized).
//
// Active-low synchronous reset. See docs/interface_contracts.md.
module stream_fifo #(
    parameter int DATA_W = 16,
    parameter int DEPTH  = 8
) (
    input  logic                            clk,
    input  logic                            rst_n,
    input  logic [DATA_W-1:0]               s_data,
    input  logic                            s_valid,
    output logic                            s_ready,
    output logic [DATA_W-1:0]               m_data,
    output logic                            m_valid,
    input  logic                            m_ready,
    output logic [$clog2(DEPTH+1)-1:0]     occupancy
);
    localparam int PTR_W = (DEPTH > 1) ? $clog2(DEPTH) : 1;
    localparam int CNT_W = $clog2(DEPTH+1);

    logic [DATA_W-1:0] storage [0:DEPTH-1];
    logic [PTR_W-1:0] write_ptr, read_ptr;
    logic [CNT_W-1:0] count;
    logic push, pop;

    assign s_ready   = (count < CNT_W'(DEPTH));
    assign m_valid   = (count > 0);
    assign m_data    = storage[read_ptr];
    assign occupancy = count;
    assign push      = s_valid && s_ready;
    assign pop       = m_valid && m_ready;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            write_ptr <= '0;
            read_ptr  <= '0;
            count     <= '0;
        end else begin
            if (push) begin
                storage[write_ptr] <= s_data;
                write_ptr <= (write_ptr == PTR_W'(DEPTH-1)) ? '0 : write_ptr + 1'b1;
            end
            if (pop)
                read_ptr <= (read_ptr == PTR_W'(DEPTH-1)) ? '0 : read_ptr + 1'b1;
            case ({push, pop})
                2'b10: count <= count + 1'b1;
                2'b01: count <= count - 1'b1;
                default: count <= count;
            endcase
        end
    end
`ifndef SYNTHESIS
    initial begin
        if (DEPTH < 1 || DATA_W < 1) $fatal(1, "Invalid FIFO parameters");
    end
    assert property (@(posedge clk) disable iff (!rst_n) count <= CNT_W'(DEPTH));
    assert property (@(posedge clk) disable iff (!rst_n)
        m_valid && !m_ready |=> m_valid && $stable(m_data));
`endif
endmodule
