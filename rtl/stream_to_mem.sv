`timescale 1ns/1ps
// Elastic 16-bit sample + sideband to 64-bit memory record packing.
module stream_to_mem (
    input logic clk, rst_n,
    input logic [15:0] s_sample,
    input logic [31:0] s_seq,
    input logic [14:0] s_frame,
    input logic s_last, s_valid,
    output logic s_ready,
    output logic [63:0] m_data,
    output logic m_valid,
    input logic m_ready
);
    assign s_ready = !m_valid || m_ready;
    always_ff @(posedge clk) begin
        if (!rst_n) begin m_valid <= 0; m_data <= 0; end
        else if (s_ready) begin
            m_valid <= s_valid;
            if (s_valid) m_data <= {s_frame, s_last, s_seq, s_sample};
        end
    end
endmodule
