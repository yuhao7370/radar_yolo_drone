`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2019/05/24 00:27:58
// Design Name: 
// Module Name: system_dma_top
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


module system_dma_top(
  inout [14:0]DDR_addr,
  inout [2:0]DDR_ba,
  inout DDR_cas_n,
  inout DDR_ck_n,
  inout DDR_ck_p,
  inout DDR_cke,
  inout DDR_cs_n,
  inout [3:0]DDR_dm,
  inout [31:0]DDR_dq,
  inout [3:0]DDR_dqs_n,
  inout [3:0]DDR_dqs_p,
  inout DDR_odt,
  inout DDR_ras_n,
  inout DDR_reset_n,
  inout DDR_we_n,
  inout FIXED_IO_ddr_vrn,
  inout FIXED_IO_ddr_vrp,
  inout [53:0]FIXED_IO_mio,
  inout FIXED_IO_ps_clk,
  inout FIXED_IO_ps_porb,
  inout FIXED_IO_ps_srstb,

  input rx_cn,//UART输入
  input clk,//时钟输入，100MHz
  input rst,
  output spi_le1,
  output spi_le2,
  output spi_data,
  output spi_clk,
  output sta_led,//常亮，用于确定状态是否为0
  output sel_led,//用于确定最后一次sel的值，为SPI设备1时亮起

  input spi_data_a_1,
  input spi_data_b_1,
  output spi_clk_1,
  output spi_cs_1,

  input spi_data_a_2,
  input spi_data_b_2,
  output spi_clk_2,
  output spi_cs_2,

  input muxout



);
  //以下是读取信号
  wire finish_1;
  wire [15:0] data_a_1;
  wire [15:0] data_b_1;
  wire finish_2;
  wire [15:0] data_a_2;
  wire [15:0] data_b_2; 
top top1(
    .rx_cn(rx_cn),//UART输入
    .clk(clk),//时钟输入，100MHz
    .rst(rst),
    .spi_le1(spi_le1),
    .spi_le2(spi_le2),
    .spi_data(spi_data),
    .spi_clk(spi_clk),
    .sta_led(sta_led),//常亮，用于确定状态是否为0
    .sel_led(sel_led),//用于确定最后一次sel的值，为SPI设备1时亮起

    .spi_data_a_1(spi_data_a_1),
    .spi_data_b_1(spi_data_b_1),
    .spi_clk_1(spi_clk_1),
    .spi_cs_1(spi_cs_1),

    .spi_data_a_2(spi_data_a_2),
    .spi_data_b_2(spi_data_b_2),
    .spi_clk_2(spi_clk_2),
    .spi_cs_2(spi_cs_2),

    .muxout_pulse(muxout),

    .finish_1(finish_1),
    .data_a_1(data_a_1),
    .data_b_1(data_b_1),
    .finish_2(finish_2),
    .data_a_2(data_a_2),
    .data_b_2(data_b_2)   
);



    //reg [63:1]din;
    (*mark_debug="true"*)wire [63:0]din;
    (*mark_debug="true"*)wire wr_clk;
    (*mark_debug="true"*)wire rd_clk;
    (*mark_debug="true"*)wire [31:0]dout;
    (*mark_debug="true"*)wire full;
    (*mark_debug="true"*)wire empty;
    (*mark_debug="true"*)wire prog_full;
    (*mark_debug="true"*)wire fifo_rst;
    (*mark_debug="true"*)reg wr_en;
    (*mark_debug="true"*)reg rd_en;
    wire wr_rst_busy;
    wire rd_rst_busy;

    assign wr_clk=!finish_1;//finished下降沿时信号稳定
    assign fifo_rst=!gpio_rtl_tri_o;
    //assign din={data_a_1,data_b_1,data_a_2,data_b_2};
   
    assign rd_clk = !FCLK_CLK0_div_4;

    reg [15:0] cnt;
 assign din={data_b_2[15:8],data_b_2[7:1],1'b1,data_a_2[15:8],data_a_2[7:1],1'b0,data_b_1[15:8],data_b_1[7:1],1'b0,data_a_1[15:8],data_a_1[7:1],1'b0};
//assign din={16'h1122,16'h3344,16'h5566,16'h7788};


    always @(posedge wr_clk or negedge gpio_rtl_tri_o or posedge full) begin
      if(!gpio_rtl_tri_o)
      begin
        wr_en <= 0;
        cnt <= 0;
      end
      else
      begin
          if(full)//满了就等
          begin
            wr_en <= 0;
          end
          else
          begin
            wr_en <= 1;
            cnt<=cnt+1;
          end
      end
      
    end

    fifo_generator_0 fifo1(
      .rst(fifo_rst),
      .wr_clk(wr_clk),
      .rd_clk(rd_clk),
      .din(din),
      .wr_en(wr_en),
      .rd_en(rd_en),
      .dout(dout),
      .full(full),
      .empty(empty),
      .prog_full(prog_full),
      .wr_rst_busy(wr_rst_busy),
      .rd_rst_busy(rd_rst_busy)
    );
    

    /*
  PORT (
    rst : IN STD_LOGIC;
    wr_clk : IN STD_LOGIC;
    rd_clk : IN STD_LOGIC;
    din : IN STD_LOGIC_VECTOR(63 DOWNTO 0);
    wr_en : IN STD_LOGIC;
    rd_en : IN STD_LOGIC;
    dout : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
    full : OUT STD_LOGIC;
    empty : OUT STD_LOGIC;
    prog_full : OUT STD_LOGIC;
    wr_rst_busy : OUT STD_LOGIC;
    rd_rst_busy : OUT STD_LOGIC
  );
    */
  
div_4 div_4_2(
    .clk(FCLK_CLK0),
    .rst(rst),
    .clk_div_4(FCLK_CLK0_div_4)
    );

 (*mark_debug="true"*) wire [31:0]S_AXIS_tdata;
 (*mark_debug="true"*) reg  S_AXIS_tlast;
 (*mark_debug="true"*) reg S_AXIS_tvalid; 
(*mark_debug="true"*)wire FCLK_CLK0_div_4;
  wire s_axis_aclk;
  wire s_axis_aresetn;
  wire [3:0]S_AXIS_tkeep;
  (*mark_debug="true"*) wire S_AXIS_tready;
 (*mark_debug="true"*)wire [0:0]gpio_rtl_tri_o;
  wire [0:0]peripheral_aresetn;
 (*mark_debug="true"*) reg [2:0] state;


  
assign S_AXIS_tkeep = 4'b1111;  
assign s_axis_aclk =  FCLK_CLK0_div_4;
assign s_axis_aresetn = gpio_rtl_tri_o;

reg finish_reg;
reg [31:0] to_send[1:0];
reg [1:0] send_bit;
(*mark_debug="true"*)reg [13:0]wr_cnt;

assign S_AXIS_tdata = dout;


always@(negedge FCLK_CLK0_div_4 or negedge gpio_rtl_tri_o)
   begin
       if(!gpio_rtl_tri_o) begin
           S_AXIS_tvalid <= 1'b0;
           //S_AXIS_tdata <= 32'd0;
           S_AXIS_tlast <= 1'b0;
           state <=0;
           rd_en <= 0;
           wr_cnt <= 0;
       end
       else begin
          case(state)
            0: begin
                if(gpio_rtl_tri_o && S_AXIS_tready && prog_full) begin
                   S_AXIS_tvalid <= 1'b1;
                   rd_en <= 1;
                   state <= 1;
                   wr_cnt <= 0;
                end
                else begin
                   S_AXIS_tvalid <= 1'b0;
                   rd_en <= 0;
                   state <= 0;
                end
              end
            1:begin
                 if(S_AXIS_tready) begin
                     if(wr_cnt >= (10240-2)) begin
                        S_AXIS_tlast <= 1'b1;
                        state <= 2;
                        wr_cnt <= 0;
                        rd_en <= 1;
                     end
                     else begin
                        S_AXIS_tlast <= 1'b0;
                        state <= 1;
                        wr_cnt <= wr_cnt+1;
                        rd_en <= 1;
                     end
                 end
                 else begin
                    rd_en <= 0;                 
                    state <= 1;
                 end
              end       
            2:begin
                 if(!S_AXIS_tready) begin
                    rd_en <= 0;
                    S_AXIS_tvalid <= 1'b1;
                    S_AXIS_tlast <= 1'b1;
                    state <= 2;
                 end
                 else begin
                    S_AXIS_tvalid <= 1'b0;
                    S_AXIS_tlast <= 1'b0;
                    rd_en <= 0;
                    //S_AXIS_tdata <= 32'd0;
                    state <= 0;
                    rd_en <= 0;
                 end
              end
           default: state <=0;
           endcase
       end              
   end  



  system system_i
       (.DDR_addr(DDR_addr),
        .DDR_ba(DDR_ba),
        .DDR_cas_n(DDR_cas_n),
        .DDR_ck_n(DDR_ck_n),
        .DDR_ck_p(DDR_ck_p),
        .DDR_cke(DDR_cke),
        .DDR_cs_n(DDR_cs_n),
        .DDR_dm(DDR_dm),
        .DDR_dq(DDR_dq),
        .DDR_dqs_n(DDR_dqs_n),
        .DDR_dqs_p(DDR_dqs_p),
        .DDR_odt(DDR_odt),
        .DDR_ras_n(DDR_ras_n),
        .DDR_reset_n(DDR_reset_n),
        .DDR_we_n(DDR_we_n),
        .FCLK_CLK0(FCLK_CLK0),
        .FIXED_IO_ddr_vrn(FIXED_IO_ddr_vrn),
        .FIXED_IO_ddr_vrp(FIXED_IO_ddr_vrp),
        .FIXED_IO_mio(FIXED_IO_mio),
        .FIXED_IO_ps_clk(FIXED_IO_ps_clk),
        .FIXED_IO_ps_porb(FIXED_IO_ps_porb),
        .FIXED_IO_ps_srstb(FIXED_IO_ps_srstb),
        .S_AXIS_tdata(S_AXIS_tdata),
        .S_AXIS_tkeep(S_AXIS_tkeep),
        .S_AXIS_tlast(S_AXIS_tlast),
        .S_AXIS_tready(S_AXIS_tready),
        .S_AXIS_tvalid(S_AXIS_tvalid),
        .gpio_rtl_tri_o(gpio_rtl_tri_o),
        .peripheral_aresetn(peripheral_aresetn),
        .s_axis_aclk(s_axis_aclk),
        .s_axis_aresetn(s_axis_aresetn));
endmodule
