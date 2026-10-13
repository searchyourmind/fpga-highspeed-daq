`timescale 1ns/1ps
module dma_writer #(parameter int RING_WORDS=32) (
    input logic clk, rst_n, start,
    input logic [31:0] base,
    input logic [15:0] start_index, length,
    input logic [63:0] s_data,
    input logic s_valid,
    output logic s_ready,
    output logic cmd_valid,
    input logic cmd_ready,
    output logic [31:0] cmd_addr,
    output logic [63:0] cmd_data,
    input logic rsp_valid, rsp_error,
    output logic rsp_ready,
    output logic busy, done, error
);
    logic waiting;
    logic [15:0] index, left;
    logic [31:0] ring_base;
    assign cmd_valid = busy && !waiting && s_valid;
    assign s_ready = busy && !waiting && cmd_ready;
    assign cmd_addr = ring_base + {13'b0,index,3'b0};
    assign cmd_data = s_data;
    assign rsp_ready = busy && waiting;
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            busy<=0; done<=0; error<=0; waiting<=0; index<=0; left<=0; ring_base<=0;
        end else begin
            done<=0;
            if (start && !busy) begin
                busy<=1; error<=0; waiting<=0; index<=start_index; left<=length; ring_base<=base;
            end else if (busy) begin
                if (cmd_valid && cmd_ready) waiting<=1;
                if (rsp_valid && rsp_ready) begin
                    waiting<=0;
                    if (rsp_error || left==1) begin busy<=0; done<=1; error<=rsp_error; end
                    else begin
                        left<=left-1'b1;
                        index <= (index==16'(RING_WORDS-1)) ? 16'd0 : index+1'b1;
                    end
                end
            end
        end
    end
endmodule
