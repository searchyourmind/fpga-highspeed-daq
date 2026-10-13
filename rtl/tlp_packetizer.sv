`timescale 1ns/1ps
// Custom memory-write transaction beats, NOT wire-format PCIe TLPs.
module tlp_packetizer #(parameter int MAX_WORDS=4) (
    input logic clk, rst_n, start,
    input logic [63:0] host_base,
    input logic [15:0] tag, length,
    input logic [63:0] s_data,
    input logic s_valid, s_last,
    output logic s_ready,
    output logic [63:0] m_data, m_addr,
    output logic [15:0] m_tag, m_length,
    output logic m_valid, m_sop, m_eop, m_last,
    input logic m_ready
);
    logic [15:0] packet_offset, packet_words, total_left;
    logic [63:0] packet_addr, next_packet_addr;
    logic [15:0] active_tag;
    // Bound each custom memory-write packet by payload size and a 4 KiB page.
    // This borrows a transaction rule; the envelope is still not wire-format PCIe.
    function automatic logic [15:0] packet_size(
        input logic [15:0] remaining, input logic [8:0] word_offset
    );
        logic [15:0] bounded, page_words;
        begin
            bounded = (remaining < 16'(MAX_WORDS)) ? remaining : 16'(MAX_WORDS);
            page_words = 16'd512 - {7'b0, word_offset};
            packet_size = (bounded < page_words) ? bounded : page_words;
        end
    endfunction
    assign next_packet_addr = packet_addr+{45'b0,packet_words,3'b0};
    assign s_ready = !m_valid || m_ready;
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            packet_offset<=0; packet_words<=0; total_left<=0;
            packet_addr<=0; active_tag<=0; m_valid<=0; m_data<=0;
            m_addr<=0; m_tag<=0; m_length<=0; m_sop<=0; m_eop<=0; m_last<=0;
        end else begin
            if (start) begin
                packet_offset<=0; total_left<=length; packet_addr<=host_base; active_tag<=tag;
                packet_words <= packet_size(length, host_base[11:3]);
            end
            if (s_ready) begin
                m_valid<=s_valid;
                if (s_valid) begin
                    m_data<=s_data; m_addr<=packet_addr; m_tag<=active_tag;
                    m_length<=packet_words<<3; m_sop<=(packet_offset==0);
                    m_eop <= (packet_offset==packet_words-1'b1); m_last<=s_last;
                    total_left<=total_left-1'b1;
                    if (packet_offset==packet_words-1'b1) begin
                        packet_offset<=0; packet_addr<=next_packet_addr;
                        packet_words <= packet_size(total_left-1'b1,
                            next_packet_addr[11:3]);
                    end else packet_offset<=packet_offset+1'b1;
                end
            end
        end
    end
`ifndef SYNTHESIS
    initial assert (MAX_WORDS >= 1 && MAX_WORDS <= 512)
        else $fatal(1, "MAX_WORDS must be 1..512");
    assert property (@(posedge clk) disable iff (!rst_n)
        m_valid |-> ({5'b0,m_addr[11:0]}+{1'b0,m_length} <= 17'd4096));
    assert property (@(posedge clk) disable iff (!rst_n)
        m_valid && !m_ready |=> m_valid && $stable({m_data,m_addr,m_tag,m_length,m_sop,m_eop,m_last}));
`endif
endmodule
