`timescale 1ns/1ps

// 8N1 UART transmitter, LSB first, with a ready/valid byte input.
// tx is driven directly from a register, so it never glitches.
module uart_tx #(
    parameter int CLKS_PER_BIT = 217
) (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] s_data,
    input  logic       s_valid,
    output logic       s_ready,
    output logic       tx
);
    logic [9:0]  shift;
    logic [3:0]  bits_left;
    logic [15:0] tick;

    assign s_ready = (bits_left == 0);
    assign tx      = shift[0];

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            shift     <= '1;
            bits_left <= '0;
            tick      <= '0;
        end else if (s_ready) begin
            if (s_valid) begin
                shift     <= {1'b1, s_data, 1'b0};
                bits_left <= 4'd10;
                tick      <= 16'(CLKS_PER_BIT - 1);
            end
        end else if (tick != 0) begin
            tick <= tick - 1'b1;
        end else begin
            shift     <= {1'b1, shift[9:1]};
            bits_left <= bits_left - 1'b1;
            tick      <= 16'(CLKS_PER_BIT - 1);
        end
    end
`ifndef SYNTHESIS
    initial begin
        if (CLKS_PER_BIT < 2 || CLKS_PER_BIT > 65535) $fatal(1, "CLKS_PER_BIT must be 2..65535");
    end
`endif
endmodule
