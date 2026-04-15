`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/03/09 13:15:57
// Design Name: 
// Module Name: autospi
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

/*
功能：自动配置默认寄存器值
注意：提供的时钟不要超过25MHz（可以是25MHz）

*/
module autospi(
        input clk,//模块时钟，下降沿触发
        input rst,//模块复位信号，下降沿触发
        output spi_le1,//SPI设备1（ADF415X）片选信号
        output spi_le2,//SPI设备2（MMIC）片选信号        
        output spi_data,//SPI信号线
        output spi_clk //SPI时钟线
    );
    reg [4:0] sta;
    reg sel;//选择对哪个器件编程，0表示SPI设备1，1表示SPI设备2
    reg [31:0] data;
    reg start;
    wire finish;
    reg[32:0] reg_data[13:0];//默认配置表，最高位为sel
    reg [27:0] delay;//24位延迟计数器，用于上电延迟
    reg [1:0] send_sta;//发送状态
    reg [1:0] send_cnt;

    spi_write spi_write2(
        .data(data),
        .clk(clk),
        .rst(rst),
        .start(start),
        .finish(finish),
        .spi_le1(spi_le1),
        .spi_le2(spi_le2),
        .sel(sel),
        .spi_data(spi_data),
        .spi_clk(spi_clk)

    );
    always @(negedge clk or negedge rst) begin
        if(!rst)
        begin
            //先按顺序配置ADF415X。寄存器顺序：7 6 6- 5 5- 4 3 2 1 0
            reg_data[0][32] <= 0; reg_data[0][31:0] <= 32'h7;//R7
            reg_data[1][32] <= 0; reg_data[1][31:0] <= 32'h17706;//R6
            reg_data[2][32] <= 0; reg_data[2][31:0] <= 32'h800006;//R6-
            reg_data[3][32] <= 0; reg_data[3][31:0] <= 32'h82225;//R5
            reg_data[4][32] <= 0; reg_data[4][31:0] <= 32'h800005;//R5-
            reg_data[5][32] <= 0; reg_data[5][31:0] <= 32'h80780084;//R4
            reg_data[6][32] <= 0; reg_data[6][31:0] <= 32'h4003;//R3
            reg_data[7][32] <= 0; reg_data[7][31:0] <= 32'hF108052;//R2
            reg_data[8][32] <= 0; reg_data[8][31:0] <= 32'h1;//R1
            reg_data[9][32] <= 0; reg_data[9][31:0] <= 32'hF812C000;//R0
            //再配置MMIC
            reg_data[10][32] <= 1; reg_data[10][31:0] <= 32'h00000ff8;
            reg_data[11][32] <= 1; reg_data[11][31:0] <= 32'h03ff800a;
            reg_data[12][32] <= 1; reg_data[12][31:0] <= 32'h03ff800b;
            reg_data[13][32] <= 1; reg_data[13][31:0] <= 32'h00000806;  

            sta <= 0;
            sel <= 0;
            data <= 32'h0;
            start <= 1;
            delay <= 28'h0;
            send_sta <= 0;
            send_cnt <= 2'b0;
        end
        else if(sta == 0)//上电延时
        begin
            //if(delay < 24'hffffff)
            if(delay < 12500000)
            begin
                delay <= delay +28'h1;
            end
            else
            begin
                sta <= 1;
                send_sta <= 0;
            end
        end
        else if(sta >= 1 && sta <= 14)
        begin
            if(send_sta==0)//准备发送
            begin
                sel <= reg_data[sta-1][32];
                data <= reg_data[sta-1][31:0];
                start <= 0;
                send_sta <= 1;
            end
            else if(send_sta==1)
            begin
                send_sta <= 2;
            end
            else 
            begin
                start <= 1;
                if(!finish)//还没发完
                begin
                    send_sta <= send_sta;
                end
                else//发送完成
                begin
                    send_sta <=0;
                    sta <= sta+1;
                end
            end
        end
        else if(sta == 15)
        begin
            if(send_cnt==2'b11)
            begin
                sta <= 15;
            end
            else
            begin
                sta <= 0;
                send_cnt <= send_cnt + 1;
            end
        end
        else 
        begin
            sta <= 0;
            sel <= 0;
            data <= 32'h0;
            start <= 1;
            delay <= 24'h0;
            send_sta <= 0;
            send_cnt <= 0;
        end
        
    end

endmodule
