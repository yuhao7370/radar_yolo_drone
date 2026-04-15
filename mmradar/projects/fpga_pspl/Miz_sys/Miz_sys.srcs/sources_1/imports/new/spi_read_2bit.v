`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/03/10 13:46:54
// Design Name: 
// Module Name: spi_read_2bit
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

//注意！！clk频率/34=采样率
module spi_read_2bit(
    input rst,
    input clk,
    input spi_data_a,
    input spi_data_b,
    output spi_clk,
    output reg spi_cs,
    output reg finish,//上升沿即读取完成
    output reg [15:0] data_a,
    output reg [15:0] data_b,
    input muxout
    );

    reg [5:0] sta;
    reg [15:0] data_a_buf;
    reg [15:0] data_b_buf;
    assign spi_clk = clk;
    always @(negedge clk or negedge rst) begin
        if(!rst)
        begin
            sta <= 0;
            data_a_buf <= 0;
            data_b_buf <= 0;
            data_a <= 0;
            data_b <= 0;
            spi_cs <= 1;
            finish <= 0;
        end
        else
        begin
            if (sta==0) begin
                sta <= sta + 1;
                spi_cs <= 0;//准备开始读
            end
            else if(sta >= 1  && sta <= 16)
            begin
                sta <= sta + 1;
            end
            else if(sta>=17 && sta<= 32)
            begin
                finish <= 0;//在中间位置置0，防止保持时间不够，可以为模块顶层调用省去很多麻烦
                data_a_buf[32-sta] <= spi_data_a;
                data_b_buf[32-sta] <= spi_data_b;
                sta <= sta + 1;
                spi_cs <= 0;
                if(sta == 32)
                begin
                    spi_cs <= 1;
                end
            end
            else if(sta == 33)//空读，预留用于满足时序
            begin
                finish <= 1;
                data_a[15:2] <= data_a_buf[15:2];
                data_b[15:2] <= data_b_buf[15:2];
                data_a[1:0] <= {muxout,muxout};
                data_b[1:0] <= {muxout,muxout};
                spi_cs <= 0;
                sta <= 1;//注意，直接到1
            end
            else
            begin
                sta <= 0;
                data_a_buf <= 0;
                data_b_buf <= 0;
                data_a <= 0;
                data_b <= 0;
                spi_cs <= 1;
                finish <= 0;
            end

        end
        
    end

endmodule
