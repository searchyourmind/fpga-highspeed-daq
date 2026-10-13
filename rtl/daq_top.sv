`timescale 1ns/1ps
module daq_top #(parameter int RING_WORDS=32, MEM_BYTES=4096, FIFO_DEPTH=8, MAX_WORDS=4) (
    input logic clk, rst_n,
    input logic desc_valid,
    output logic desc_ready,
    input logic [15:0] desc_id, desc_start, desc_length,
    input logic [31:0] desc_base,
    input logic [63:0] desc_host,
    input logic desc_owner,
    input logic [15:0] frame_len,
    input logic [7:0] gain,
    output logic comp_valid,
    input logic comp_ready,
    output logic [15:0] comp_id,
    output logic [2:0] comp_status,
    output logic mem_cmd_valid, mem_cmd_write,
    input logic mem_cmd_ready,
    output logic [31:0] mem_cmd_addr,
    output logic [63:0] mem_cmd_data,
    input logic mem_rsp_valid, mem_rsp_error,
    input logic [63:0] mem_rsp_data,
    output logic mem_rsp_ready,
    output logic [63:0] link_data, link_addr,
    output logic [15:0] link_tag, link_length,
    output logic link_valid, link_sop, link_eop, link_last,
    input logic link_ready,
    output logic [$clog2(FIFO_DEPTH+1)-1:0] fifo_occupancy
);
    logic job_valid, job_ready, job_done, job_error, launch;
    logic [15:0] job_id, job_start, job_length;
    logic [31:0] job_base;
    logic [63:0] job_host;
    typedef enum logic [2:0] {IDLE, WRITE, READ_START, READ, DRAIN, FINISH} phase_t;
    phase_t phase;
    logic [63:0] stream_data, read_data;
    logic stream_valid, stream_ready, read_valid, read_ready, read_last;
    logic write_done, write_error, read_done, read_error;
    logic w_cmd_valid, w_rsp_ready, r_cmd_valid, r_rsp_ready;
    logic [31:0] w_addr, r_addr;
    logic [63:0] w_data;
    logic pipeline_rst_n;
    logic [15:0] active_frame_len;
    logic [7:0] active_gain;
    always_ff @(posedge clk) begin
        if (!rst_n) begin active_frame_len<=1; active_gain<=0; end
        else if (desc_valid && desc_ready) begin active_frame_len<=frame_len; active_gain<=gain; end
    end
    assign job_ready=(phase==IDLE);
    assign launch=job_valid && job_ready;
    assign job_done=(phase==FINISH);
    // Flush buffered samples after an error, before accepting another descriptor.
    assign pipeline_rst_n=rst_n && !(phase==FINISH);
    dma_descriptor #(.RING_WORDS(RING_WORDS),.MEM_BYTES(MEM_BYTES)) descriptors_i(
        .clk,.rst_n,.desc_valid,.desc_ready,.desc_id,.desc_start,.desc_length,.desc_base,.desc_host,.desc_owner,
        .job_valid,.job_ready,.job_id,.job_start,.job_length,.job_base,.job_host,.job_done,.job_error,
        .comp_valid,.comp_ready,.comp_id,.comp_status);
    streaming_top #(.FIFO_DEPTH(FIFO_DEPTH)) stream_i(.clk,.rst_n(pipeline_rst_n),.start(launch),
        .sample_count({16'b0,job_length}),.frame_len(active_frame_len),.gain(active_gain),.m_data(stream_data),.m_valid(stream_valid),
        .m_ready(stream_ready),.occupancy(fifo_occupancy));
    dma_writer #(.RING_WORDS(RING_WORDS)) writer_i(.clk,.rst_n,.start(launch),.base(job_base),
        .start_index(job_start),.length(job_length),.s_data(stream_data),.s_valid(stream_valid),.s_ready(stream_ready),
        .cmd_valid(w_cmd_valid),.cmd_ready(mem_cmd_ready && phase==WRITE),.cmd_addr(w_addr),.cmd_data(w_data),
        .rsp_valid(mem_rsp_valid && phase==WRITE),.rsp_error(mem_rsp_error),.rsp_ready(w_rsp_ready),
        .busy(),.done(write_done),.error(write_error));
    dma_reader #(.RING_WORDS(RING_WORDS)) reader_i(.clk,.rst_n,.start(phase==READ_START),.base(job_base),
        .start_index(job_start),.length(job_length),.cmd_valid(r_cmd_valid),.cmd_ready(mem_cmd_ready && phase==READ),
        .cmd_addr(r_addr),.rsp_valid(mem_rsp_valid && phase==READ),.rsp_error(mem_rsp_error),.rsp_data(mem_rsp_data),
        .rsp_ready(r_rsp_ready),.m_data(read_data),.m_valid(read_valid),.m_last(read_last),.m_ready(read_ready),
        .busy(),.done(read_done),.error(read_error));
    tlp_packetizer #(.MAX_WORDS(MAX_WORDS)) packetizer_i(.clk,.rst_n(pipeline_rst_n),.start(launch),
        .host_base(job_host),.tag(job_id),.length(job_length),.s_data(read_data),.s_valid(read_valid),.s_last(read_last),
        .s_ready(read_ready),.m_data(link_data),.m_addr(link_addr),.m_tag(link_tag),.m_length(link_length),
        .m_valid(link_valid),.m_sop(link_sop),.m_eop(link_eop),.m_last(link_last),.m_ready(link_ready));
    assign mem_cmd_valid=(phase==WRITE) ? w_cmd_valid : (phase==READ && r_cmd_valid);
    assign mem_cmd_write=(phase==WRITE);
    assign mem_cmd_addr=(phase==WRITE) ? w_addr : r_addr;
    assign mem_cmd_data=w_data;
    assign mem_rsp_ready=(phase==WRITE) ? w_rsp_ready : (phase==READ && r_rsp_ready);
    always_ff @(posedge clk) begin
        if (!rst_n) begin phase<=IDLE; job_error<=0; end
        else case(phase)
            IDLE: if (launch) begin phase<=WRITE; job_error<=0; end
            WRITE: if (write_done) begin
                if (write_error) begin job_error<=1; phase<=FINISH; end
                else phase<=READ_START;
            end
            READ_START: phase<=READ;
            READ: if (read_done) begin
                if (read_error) begin job_error<=1; phase<=FINISH; end
                else phase<=DRAIN;
            end
            DRAIN: if (!link_valid || (link_valid && link_ready)) phase<=FINISH;
            FINISH: phase<=IDLE;
            default: phase<=IDLE;
        endcase
    end
`ifndef SYNTHESIS
    assert property (@(posedge clk) disable iff (!rst_n)
        mem_cmd_valid && !mem_cmd_ready |=> mem_cmd_valid && $stable({mem_cmd_write,mem_cmd_addr,mem_cmd_data}));
`endif
endmodule
