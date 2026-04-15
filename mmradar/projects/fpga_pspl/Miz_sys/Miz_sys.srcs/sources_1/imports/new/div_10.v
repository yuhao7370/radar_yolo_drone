`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/03/10 13:23:07
// Design Name: 
// Module Name: div_10
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

//通过计数器实现10分频
module div_10(
    input clk,
    input rst,
    output reg clk_div_10
    );

    reg [2:0]clk_cnt;
    always @(negedge clk or negedge rst) begin
        if(!rst)
        begin
            clk_cnt <= 3'b0;
            clk_div_10 <= 1;
        end
        else
        begin
            if(clk_cnt >= (10/2-1) )
            begin
                clk_cnt <= 3'b0;
                clk_div_10 <= !clk_div_10;
            end
            else
            begin
                clk_cnt <= clk_cnt+1;
            end
            
        end
    end
    assign clk_div_4 = clk_cnt[1];
endmodule
