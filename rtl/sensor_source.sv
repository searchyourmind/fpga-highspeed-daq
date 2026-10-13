`timescale 1ns/1ps
module sensor_source (
    input logic clk, rst_n, start,
    input logic [31:0] sample_count,
    input logic [15:0] frame_len,
    output logic [63:0] m_data,
    output logic m_valid,
    input logic m_ready,
    output logic busy, done
);
    logic [31:0] seq, limit;
    logic [15:0] position, frame_size;
    logic [14:0] frame_id;
    logic last;
    assign last = (position == frame_size-1'b1) || (seq == limit-1'b1);
    assign m_data = {frame_id, last, seq, 16'(seq * 32'd73 + 32'd19)};
    assign m_valid = busy;
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            busy <= 0; done <= 0; seq <= 0; limit <= 0;
            position <= 0; frame_size <= 1; frame_id <= 0;
        end else begin
            done <= 0;
            if (start && !busy) begin
                seq <= 0; position <= 0; frame_id <= 0;
                limit <= sample_count;
                frame_size <= (frame_len == 0) ? 16'd1 : frame_len;
                busy <= (sample_count != 0);
                done <= (sample_count == 0);
            end else if (m_valid && m_ready) begin
                seq <= seq + 1'b1;
                if (last) begin position <= 0; frame_id <= frame_id + 1'b1; end
                else position <= position + 1'b1;
                if (seq == limit-1'b1) begin busy <= 0; done <= 1; end
            end
        end
    end
`ifndef SYNTHESIS
    assert property (@(posedge clk) disable iff (!rst_n)
        m_valid && !m_ready |=> m_valid && $stable(m_data));
`endif
endmodule
