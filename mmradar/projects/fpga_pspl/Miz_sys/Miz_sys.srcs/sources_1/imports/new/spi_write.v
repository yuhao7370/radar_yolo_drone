`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/03/07 15:30:00
// Design Name: 
// Module Name: spi_write
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

//功能：生成SPI写时序，用于写寄存器（32bit）
module spi_write(
    input [31:0] data,//32位待写入数据，高位先发，在start下降沿被所存直到写入结束
    input clk,//模块时钟，下降沿触发
    input rst,//模块复位信号，下降沿触发
    input start,//开始传输，下降沿触发
    output reg finish,//完成传输标志，上升沿
    output reg spi_le1,//SPI设备1片选信号，常高
    output reg spi_le2,//SPI设备2片选信号，常高
    input sel,//选择对哪个器件编程，0表示SPI设备1，1表示SPI设备2
    output reg spi_data,//SPI信号线，常高
    output reg spi_clk //SPI时钟线，常低
    );
    reg [31:0] to_send;//所存待发数据
    reg [5:0] sta;//状态机
    reg start_flag;//记录上一时刻的start,为了实现start下降沿触发



    always @(negedge clk or negedge rst) begin
        if(!rst)
        begin
            /*SPI接口电平初始化*/
            spi_le1 <= 1'b1;
            spi_le2 <= 1'b1;
            spi_data <= 1'b1;
            spi_clk <= 1'b0;
            
            /*完成标志初始化*/
            finish <= 1'b0;

            /*状态初始化*/
            to_send <= 32'h00000000;
            sta <= 6'b000000;

            start_flag <= start;

        end
        else
        begin
            if(sta==0)//等待开始
            begin
                if(start_flag == 1 && start == 0) //检测到下降沿，准备开始发送
                begin
                    sta <= 6'b000001; //进入发送状态
                    to_send <= data; //锁存数据
                    spi_clk <= 1'b0;
                    spi_data <= data[31];//准备第一个数据
                    finish <= 1'b0;
                    if(sel)
                    begin
                        spi_le1 <= 1'b1;
                        spi_le2 <= 1'b0;
                    end
                    else
                    begin
                        spi_le1 <= 1'b0;
                        spi_le2 <= 1'b1;
                    end
                end       
                else
                begin
                    start_flag <= start;
                end        
            end
            else if(sta>=1 && sta<=32)
            begin
                if(spi_clk)
                begin
                    if(sta>=32)
                    begin
                        spi_clk <= 1'b0;
                        sta <= 6'b000000;
                        spi_le1 <= 1'b1;
                        spi_le2 <= 1'b1;
                        spi_data <= 1'b1;
                        finish <= 1'b1;

                    end
                    else
                    begin
                        spi_data <= data[31-sta];
                        spi_clk <= !spi_clk;
                        sta <= sta + 6'b000001;
                    end
                end
                else
                begin
                    spi_clk <= !spi_clk;
                end
            end
            else
            begin
                /*SPI接口电平初始化*/
                spi_le1 <= 1'b1;
                spi_le2 <= 1'b1;
                spi_data <= 1'b1;
                spi_clk <= 1'b0;
                
                /*完成标志初始化*/
                finish <= 1'b0;

                /*状态初始化*/
                to_send <= 32'h00000000;
                sta <= 6'b000000;
            end
            start_flag <= start;

            

        end


        
    end
endmodule
