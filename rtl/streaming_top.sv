`timescale 1ns/1ps
module streaming_top # (parameter int FIFO_DEPTH=8) (
    input logic clk, rst_n, start,
    input logic [31:0] sample_count,
    input logic [15:0] frame_len,
    input logic [7:0] gain,
    output logic [63:0] m_data,
    output logic m_valid,
    input logic m_ready,
    output logic [$clog2(FIFO_DEPTH+1)-1:0] occupancy
);
    logic [63:0] src_data, proc_data, fifo_data;
    logic src_valid, src_ready, proc_valid, proc_ready, fifo_valid, fifo_ready;
    logic [7:0] active_gain;
    always_ff @(posedge clk) begin
        if (!rst_n) active_gain <= 0;
        else if (start) active_gain <= gain;
    end
    sensor_source source_i(.clk, .rst_n, .start, .sample_count, .frame_len,
        .m_data(src_data), .m_valid(src_valid), .m_ready(src_ready), .busy(), .done());
    stream_processor processor_i(.clk, .rst_n, .gain(active_gain), .s_data(src_data),
        .s_valid(src_valid), .s_ready(src_ready), .m_data(proc_data), .m_valid(proc_valid), .m_ready(proc_ready));
    stream_fifo #(.DATA_W(64), .DEPTH(FIFO_DEPTH)) fifo_i(.clk, .rst_n,
        .s_data(proc_data), .s_valid(proc_valid), .s_ready(proc_ready),
        .m_data(fifo_data), .m_valid(fifo_valid), .m_ready(fifo_ready), .occupancy);
    stream_to_mem packer_i(.clk, .rst_n, .s_sample(fifo_data[15:0]), .s_seq(fifo_data[47:16]),
        .s_frame(fifo_data[63:49]), .s_last(fifo_data[48]), .s_valid(fifo_valid), .s_ready(fifo_ready),
        .m_data, .m_valid, .m_ready);
endmodule
