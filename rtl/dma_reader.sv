`timescale 1ns/1ps
module dma_reader #(parameter int RING_WORDS=32) (
    input logic clk, rst_n, start,
    input logic [31:0] base,
    input logic [15:0] start_index, length,
    output logic cmd_valid,
    input logic cmd_ready,
    output logic [31:0] cmd_addr,
    input logic rsp_valid, rsp_error,
    input logic [63:0] rsp_data,
    output logic rsp_ready,
    output logic [63:0] m_data,
    output logic m_valid, m_last,
    input logic m_ready,
    output logic busy, done, error
);
    logic waiting;
    logic [15:0] index, left;
    logic [31:0] ring_base;
    assign cmd_valid = busy && !waiting && !m_valid;
    assign cmd_addr = ring_base + {13'b0,index,3'b0};
    assign rsp_ready = busy && waiting && !m_valid;
    assign m_last = (left==1);
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            busy<=0; done<=0; error<=0; waiting<=0; index<=0; left<=0;
            ring_base<=0; m_data<=0; m_valid<=0;
        end else begin
            done<=0;
            if (start && !busy) begin
                busy<=1; error<=0; waiting<=0; index<=start_index; left<=length; ring_base<=base; m_valid<=0;
            end else if (busy) begin
                if (cmd_valid && cmd_ready) waiting<=1;
                if (rsp_valid && rsp_ready) begin
                    waiting<=0;
                    if (rsp_error) begin busy<=0; done<=1; error<=1; end
                    else begin m_data<=rsp_data; m_valid<=1; end
                end
                if (m_valid && m_ready) begin
                    m_valid<=0;
                    if (left==1) begin busy<=0; done<=1; end
                    else begin
                        left<=left-1'b1;
                        index<=(index==16'(RING_WORDS-1)) ? 16'd0 : index+1'b1;
                    end
                end
            end
        end
    end
endmodule
