`timescale 1ns/1ps

// 8N1 UART receiver, LSB first. rx is asynchronous to clk and is
// double-registered here before use. Each bit is sampled once near its middle.
// A start bit that is high at its midpoint is treated as noise and ignored; a
// frame whose stop bit is low is dropped without asserting valid.
module uart_rx #(
    parameter int CLKS_PER_BIT = 217
) (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       rx,
    output logic [7:0] data,
    output logic       valid
);
    logic       rx_meta, rx_sync;
    logic       busy;
    logic [3:0] bit_index;
    logic [15:0] tick;
    logic [7:0] shift;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            rx_meta <= 1'b1;
            rx_sync <= 1'b1;
        end else begin
            rx_meta <= rx;
            rx_sync <= rx_meta;
        end
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            busy      <= 1'b0;
            bit_index <= '0;
            tick      <= '0;
            shift     <= '0;
            data      <= '0;
            valid     <= 1'b0;
        end else begin
            valid <= 1'b0;
            if (!busy) begin
                if (!rx_sync) begin
                    // Two cycles of synchronizer delay already elapsed.
                    busy      <= 1'b1;
                    bit_index <= '0;
                    tick      <= 16'(CLKS_PER_BIT/2 - 2);
                end
            end else if (tick != 0) begin
                tick <= tick - 1'b1;
            end else begin
                tick <= 16'(CLKS_PER_BIT - 1);
                bit_index <= bit_index + 1'b1;
                if (bit_index == 0) begin
                    if (rx_sync) busy <= 1'b0;
                end else if (bit_index <= 8) begin
                    shift <= {rx_sync, shift[7:1]};
                end else begin
                    busy <= 1'b0;
                    if (rx_sync) begin
                        data  <= shift;
                        valid <= 1'b1;
                    end
                end
            end
        end
    end
`ifndef SYNTHESIS
    initial begin
        if (CLKS_PER_BIT < 8 || CLKS_PER_BIT > 65535) $fatal(1, "CLKS_PER_BIT must be 8..65535");
    end
`endif
endmodule
