# HT-Trendline
希尔伯特-瞬时趋势线策略

实现平台：BOTVS

使用的api文档：https://www.botvs.com/bbs-topic/443

策略介绍：
希尔伯特变换，本来是用于数学与信号处理领域中，是信号分析处理中的一种重要方法。它可以把信号的所有频率分量的相位推迟90度，并能有效地提取复杂信号的瞬时参数——瞬时振幅、瞬时相位和瞬时频率。
在投资市场中，将希尔伯特变换移植过来，可以对帮助对价格进行分析，产生一个瞬时趋势线。这个线类似于常用的移动均线，但延迟更低，对市场价格的变化更为迅速。
使用方法：
使用talib库的HT_TRENDLINE方法，来计算一段时间内的希尔伯特变换-瞬时趋势线（一下简称趋势线）的值。这个值与我们常用的移动平均值类似，因此策略使用方法也类似。并加入了0.015的上下轨偏离，来规避长期的小幅上下波动导致的频繁交易

本策略仅供学习参考，请勿直接复制用于实盘，不保证任何收益，对此造成的一切后果请自负。

欢迎交流 email: cningyuan@gmail.com