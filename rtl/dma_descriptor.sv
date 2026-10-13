`timescale 1ns/1ps
module dma_descriptor # (parameter int RING_WORDS=32, MEM_BYTES=4096) (
    input logic clk, rst_n,
    input logic desc_valid,
    output logic desc_ready,
    input logic [15:0] desc_id, desc_start, desc_length,
    input logic [31:0] desc_base,
    input logic [63:0] desc_host,
    input logic desc_owner,
    output logic job_valid,
    input logic job_ready,
    output logic [15:0] job_id, job_start, job_length,
    output logic [31:0] job_base,
    output logic [63:0] job_host,
    input logic job_done, job_error,
    output logic comp_valid,
    input logic comp_ready,
    output logic [15:0] comp_id,
    output logic [2:0] comp_status
);
    typedef enum logic [1:0] {IDLE, ISSUE, WAIT_JOB, COMPLETE} state_t;
    state_t state;
    logic [2:0] validation;
    always_comb begin
        validation = 0;
        if (!desc_owner) validation = 4;
        else if (desc_length == 0 || desc_length > 16'(RING_WORDS) || desc_start >= 16'(RING_WORDS)) validation = 2;
        else if (desc_base[2:0] != 0 || {1'b0,desc_base}+33'(RING_WORDS*8) > 33'(MEM_BYTES)) validation = 1;
        // The last addressed byte, rather than the exclusive end, must fit.
        else if (desc_host[2:0] != 0 || desc_host > (64'hffffffffffffffff - ({45'b0,desc_length,3'b0}-64'd1))) validation = 3;
    end
    assign desc_ready = (state == IDLE);
    assign job_valid = (state == ISSUE);
    assign comp_valid = (state == COMPLETE);
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state <= IDLE; job_id <= 0; job_start <= 0; job_length <= 0;
            job_base <= 0; job_host <= 0; comp_id <= 0; comp_status <= 0;
        end else case (state)
            IDLE: if (desc_valid) begin
                job_id <= desc_id; job_start <= desc_start; job_length <= desc_length;
                job_base <= desc_base; job_host <= desc_host;
                comp_id <= desc_id; comp_status <= validation;
                state <= (validation == 0) ? ISSUE : COMPLETE;
            end
            ISSUE: if (job_ready) state <= WAIT_JOB;
            WAIT_JOB: if (job_done) begin comp_status <= job_error ? 3'd5 : 3'd0; state <= COMPLETE; end
            COMPLETE: if (comp_ready) state <= IDLE;
            default: state <= IDLE;
        endcase
    end
`ifndef SYNTHESIS
    assert property (@(posedge clk) disable iff (!rst_n)
        comp_valid && !comp_ready |=> comp_valid && $stable({comp_id,comp_status}));
`endif
endmodule
