`timescale 1ns/1ps
module stream_processor (
    input logic clk, rst_n,
    input logic [7:0] gain,
    input logic [63:0] s_data,
    input logic s_valid,
    output logic s_ready,
    output logic [63:0] m_data,
    output logic m_valid,
    input logic m_ready
);
    logic [23:0] product;
    assign product = s_data[15:0] * gain;
    assign s_ready = !m_valid || m_ready;
    always_ff @(posedge clk) begin
        if (!rst_n) begin m_valid <= 0; m_data <= 0; end
        else if (s_ready) begin
            m_valid <= s_valid;
            if (s_valid)
                m_data <= {s_data[63:16], (|product[23:16]) ? 16'hffff : product[15:0]};
        end
    end
`ifndef SYNTHESIS
    assert property (@(posedge clk) disable iff (!rst_n)
        m_valid && !m_ready |=> m_valid && $stable(m_data));
`endif
endmodule
