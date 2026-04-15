`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/03/07 19:32:54
// Design Name: 
// Module Name: div_4
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////
//功能：通过计数器实现4分频

module div_4(
    input clk,
    input rst,
    output clk_div_4
    );
    reg [1:0]clk_cnt;
    always @(negedge clk or negedge rst) begin
        if(!rst)
        begin
            clk_cnt <= 2'b00;
        end
        else
        begin
            clk_cnt <= clk_cnt+1;
        end
    end
    assign clk_div_4 = clk_cnt[1];
endmodule
