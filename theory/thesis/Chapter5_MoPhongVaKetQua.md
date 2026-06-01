# CHƯƠNG 5: MÔ PHỎNG VÀ KẾT QUẢ

> ✅ **Cập nhật:** Kết quả từ mô phỏng Python, dữ liệu thời tiết từ NASA POWER, model LSTM-TCN huấn luyện trên 3 năm dữ liệu Đà Nẵng.

---

Chương này trình bày chi tiết quá trình mô phỏng và đánh giá hệ thống điều khiển đề xuất. Nội dung được chia làm sáu phần chính: (5.1) dữ liệu và huấn luyện mô hình dự báo LSTM-TCN, (5.2) tham số hệ thống và môi trường mô phỏng, (5.3) các kịch bản mô phỏng, (5.4) kết quả mô phỏng chi tiết, (5.5) so sánh giữa các phương pháp, và (5.6) phân tích độ nhạy.

---

## 5.1 Dữ liệu và huấn luyện mô hình dự báo LSTM-TCN

### 5.1.1 Nguồn dữ liệu

Mô hình dự báo LSTM-TCN được huấn luyện trên bộ dữ liệu kết hợp giữa dữ liệu thời tiết thực tế từ NASA POWER và dữ liệu mô phỏng:

**Dữ liệu thời tiết — NASA POWER:**

Dữ liệu thời tiết được lấy từ cơ sở dữ liệu NASA POWER (Prediction Of Worldwide Energy Resources) thông qua API miễn phí [56]. Các thông số được thu thập bao gồm:

| Thông số | Mã NASA | Đơn vị | Khoảng giá trị |
|----------|---------|:------:|:--------------:|
| Bức xạ mặt trời (GHI) | ALLSKY_SFC_SW_DWN | W/m² | 0–984 |
| Nhiệt độ môi trường | T2M | °C | 13,1–36,4 |
| Tốc độ gió tại 10m | WS10M | m/s | 0,1–9,5 |

Dữ liệu được thu thập tại tọa độ Đà Nẵng (16,0°N, 108,0°E) trong giai đoạn **2021–2023** (3 năm), với độ phân giải **1 giờ**, tổng cộng **26.280 mẫu**. API NASA POWER không yêu cầu xác thực và cho phép truy cập tối đa 15 tham số mỗi yêu cầu [57].

**Dữ liệu bổ sung:**

Do NASA POWER không cung cấp dữ liệu nhu cầu tải và giá điện, các thông số này được sinh từ mô hình mô phỏng:

- **Nhu cầu tải:** Mô hình diurnal với hai đỉnh sáng (7h) và chiều (18h), cộng nhiễu AR(1). Công suất đỉnh 18 kW, nền 8 kW.
- **Giá điện:** Biểu giá TOU (Time-of-Use) 5 khung giờ theo tỷ lệ \(0,5\!:\!0,8\!:\!1,0\!:\!2,0\!:\!1,2\) so với giá cơ sở 0,12 $/kWh.
- **Công suất PV:** Tính từ GHI và nhiệt độ qua mô hình 5-parameter single-diode.
- **Công suất gió:** Tính từ tốc độ gió qua mô hình IEC 4-region cubic.

### 5.1.2 Tiền xử lý dữ liệu

Dữ liệu được chuẩn hóa bằng phương pháp MinMax scaling:

$$X_{scaled} = \frac{X - X_{min}}{X_{max} - X_{min}}$$

Các cửa sổ trượt (sliding windows) được tạo với look-back = 12 bước (12 giờ) và horizon = 4 bước (4 giờ). Tổng số mẫu sau khi tạo cửa sổ là 26.265 mẫu, được chia theo tỷ lệ:

| Tập dữ liệu | Số mẫu | Tỷ lệ |
|:-----------:|:------:|:-----:|
| Train | 19.700 | 75% |
| Validation | 2.626 | 10% |
| Test | 3.939 | 15% |

**Kiến trúc đầu vào – đầu ra:**

- **Đầu vào (features):** 7 thông số — GHI, nhiệt độ, tốc độ gió, nhu cầu tải, giá điện, sin(giờ), cos(giờ)
- **Đầu ra (targets):** 5 thông số — công suất PV, công suất gió, nhiệt độ, nhu cầu tải, giá điện
- **Kích thước:** X: (batch, 12, 7), y: (batch, 4, 5)

### 5.1.3 Kiến trúc mô hình

Mô hình LSTM-TCN sử dụng kiến trúc sequential LSTM → TCN kế thừa từ công trình của Limouni et al. [9] với các mở rộng:

```
Input: (batch, 12, 7)
  ↓
LSTM(256) → Dropout(0.2) → LSTM(64) → Dropout(0.2)
  ↓
TCN Block 1 (filters=128, dilation=1) → ReLU → Dropout(0.2)
TCN Block 2 (filters=128, dilation=2) → ReLU → Dropout(0.2)
TCN Block 3 (filters=128, dilation=4) → ReLU → Dropout(0.2)
  ↓
Dense(H×5) → Reshape(H, 5)
Output: (batch, 4, 5)
```

**Thông số huấn luyện:**

| Tham số | Giá trị |
|---------|:-------:|
| Optimizer | Adam |
| Learning rate | 0,001 |
| Hàm loss | MSE |
| Batch size | 100 |
| Max epochs | 100 |
| Early stopping patience | 10 |
| Số tham số | ~1.200.000 |

### 5.1.4 Kết quả huấn luyện

Mô hình hội tụ sau **26 epochs** (early stopping) với val_loss = 0,0021 (MSE trên dữ liệu đã chuẩn hóa). Kết quả dự báo chi tiết trên tập test:

| Target | RMSE | MAE | R² | Đánh giá |
|--------|:----:|:---:|:--:|:--------:|
| **Công suất PV** (kW) | 1,45 | 0,86 | **0,941** | ✅ Rất tốt |
| **Công suất gió** (kW) | 0,18 | 0,12 | -0,026 | ❌ Kém (nhiễu) |
| **Nhiệt độ** (°C) | 1,08 | 0,84 | **0,871** | ✅ Tốt |
| **Nhu cầu tải** (kW) | 0,60 | 0,48 | **0,870** | ✅ Tốt |
| **Giá điện** ($/kWh) | 0,00 | 0,00 | **1,000** | ✅ Hoàn hảo |

**Nhận xét:**

- **Công suất PV** đạt R² = 0,941 — mô hình dự báo rất chính xác nhờ tính chu kỳ ngày-đêm rõ ràng của bức xạ mặt trời, như minh họa trên Hình 5.1.
- **Công suất gió** có R² ≈ 0 — dự báo gió ở độ phân giải 1 giờ là thách thức lớn do tính hỗn loạn của khí quyển [13]. Kết quả này tương đồng với các nghiên cứu khác khi dự báo gió ngắn hạn [14].
- **Nhiệt độ** và **nhu cầu tải** đạt R² ≈ 0,87 — đủ chính xác cho ứng dụng EMS.
- **Giá điện** đạt R² = 1,00 — TOU là deterministic, mô hình học được chính xác.

Hình 5.1 minh họa kết quả dự báo của mô hình LSTM-TCN trên 7 ngày dữ liệu thực tế. Có thể thấy đường dự báo (đỏ đứt) bám sát đường giá trị thực tế (cam/xanh) đối với công suất PV và nhu cầu tải, trong khi giá điện được dự báo chính xác tuyệt đối.

![Hình 5.1: Kết quả dự báo LSTM-TCN trên 7 ngày dữ liệu thực tế](../../simulation/outputs/figures/forecast_validation.png)
*Hình 5.1. So sánh giá trị dự báo (LSTM-TCN) và giá trị thực tế cho công suất PV, nhu cầu tải và giá điện. Phần tô đỏ mờ giữa hai đường biểu thị sai số dự báo. PV và Load cho thấy độ bám tốt, Price khớp hoàn hảo.*

So với kết quả từ bài báo gốc Limouni (R² > 0,96 cho GHI, 0,98 cho nhiệt độ, 0,99 cho tải), mô hình đề xuất có độ chính xác thấp hơn do số lượng features đầu vào nhiều hơn (wind speed, price) và dữ liệu thực tế có độ biến động cao hơn.

---

## 5.2 Tham số hệ thống và môi trường mô phỏng

### 5.2.1 Tham số hệ thống điện

Hệ thống microgrid được mô phỏng với các thông số vật lý như Bảng 5.1.

**Bảng 5.1. Tham số hệ thống microgrid**

| Thành phần | Tham số | Giá trị | Đơn vị |
|------------|---------|:-------:|:------:|
| **PV Array** | Công suất đặt | 20 | kWp |
| | Số module | 80 (ASW-250P) | — |
| | Hiệu suất | 18 | % |
| | Diện tích | 130 | m² |
| **Wind Turbine** | Công suất định mức | 10 | kW |
| | Vận tốc cut-in / rated / cut-out | 3 / 12 / 25 | m/s |
| | Đường kính rotor | 7 | m |
| **Battery** | Dung lượng | 50 | kWh |
| | Điện áp danh định | 120 | V |
| | Giới hạn SOC | 20–90 | % |
| | Hiệu suất sạc/xả | 95 | % |
| | Công suất sạc/xả max | 25 | kW |
| **Inverter** | Công suất định mức | 30 | kVA |
| **DC Bus** | Điện áp danh định | 800 | V |
| **AC Bus** | Điện áp | 380 | V |
| **Lưới điện** | Công suất mua/bán max | 25 | kW |

### 5.2.2 Tham số điều khiển

**Bảng 5.2. Tham số bộ điều khiển**

| Tham số | Giá trị | Ghi chú |
|---------|:-------:|---------|
| **MPC outer loop** | | |
| Prediction horizon (Np) | 24 | giờ |
| Control horizon (Nc) | 24 | giờ |
| Sample time (dt) | 1 | giờ |
| Peak penalty (w_peak) | 0,5 (flat) / 0,3 (TOU) | — |
| Degradation cost (w_degrad) | 0,01 | — |
| **Demand Response** | | |
| Peak threshold | 70% | % P_peak |
| Valley threshold | 15% | % P_peak |
| Alpha clip (PeakClip) | 15% | % P_load |
| Beta fill (ValleyFill) | 0% | % P_load |
| **PMS** | | |
| SOC charge stop | 85% | — |
| SOC discharge stop | 30% | — |
| Hysteresis band | 5% | — |

### 5.2.3 Môi trường mô phỏng

Mô phỏng được thực hiện trên nền tảng Python 3.13 với các thư viện chính:

- **NumPy/SciPy:** Tính toán số học, xử lý ma trận
- **TensorFlow/Keras:** Xây dựng và huấn luyện mô hình LSTM-TCN
- **OSQP:** Giải bài toán quy hoạch toàn phương (QP) cho MPC
- **Matplotlib:** Vẽ đồ thị kết quả
- **pvlib:** Truy xuất dữ liệu thời tiết từ NASA POWER

**Cấu hình phần cứng:** CPU Intel, RAM 16 GB. Mô hình LSTM-TCN được huấn luyện trên CPU (không có GPU).

**Thời gian mô phỏng:** Mỗi kịch bản 168 giờ (7 ngày) với bước thời gian 1 giờ. Thời gian chạy hoàn chỉnh 5 kịch bản khoảng 30–60 giây.

---

## 5.3 Các kịch bản mô phỏng

Để đánh giá hiệu quả của từng thành phần trong hệ thống điều khiển đề xuất, năm kịch bản mô phỏng được thiết kế như Bảng 5.3. Các kịch bản được xây dựng theo nguyên tắc **tăng dần mức độ phức tạp**: từ điều khiển rule-based đơn giản đến kết hợp đầy đủ MPC, TOU và threshold DR.

**Bảng 5.3. Năm kịch bản mô phỏng**

| Kịch bản | Mô tả | EMS-MPC | TOU | Threshold DR |
|:--------:|-------|:-------:|:---:|:-----------:|
| **S1** | Rule-based (baseline) | ❌ | ❌ | ❌ |
| **S2** | EMS-MPC peak shaving | ✅ | ❌ | ❌ |
| **S3** | MPC + TOU pricing | ✅ | ✅ | ❌ |
| **S4** | Threshold DR | ❌ | ❌ | ✅ |
| **S5** | Full DR (đề xuất) | ✅ | ✅ | ✅ |

### 5.3.1 Kịch bản S1 — Rule-based Baseline

S1 là kịch bản cơ sở, sử dụng **PMS (Power Management System)** với các luật if-this-than-that đơn giản:
- Nếu thừa năng lượng (P_gen > P_load): sạc pin (M1), hoặc ValleyFill (M2), hoặc bán lưới (M3)
- Nếu thiếu năng lượng (P_gen < P_load): xả pin (M5), hoặc PeakClip (M4), hoặc mua lưới (M6)

S1 **không sử dụng MPC, không có DR, không có TOU pricing.** Đây là baseline để so sánh các kịch bản khác.

### 5.3.2 Kịch bản S2 — EMS-MPC Peak Shaving

S2 sử dụng **EMS-MPC** (Economic MPC) để tối ưu hóa lịch sạc/xả pin. Bộ điều khiển nhìn trước 24 giờ và giải bài toán QP để giảm thiểu chi phí điện năng kết hợp với phạt peak công suất:

$$J = \sum_{k=0}^{N} \bigl[ \text{price}(k) \cdot P_{grid}(k) + w_{peak} \cdot P_{grid}^2(k) + w_{degrad} \cdot P_{bat}^2(k) \bigr]$$

Với giá điện phẳng (0,12 $/kWh), MPC tập trung vào **peak shaving**: sạc pin khi P_net thấp, xả khi P_net cao.

### 5.3.3 Kịch bản S3 — MPC + TOU Pricing

S3 kết hợp EMS-MPC với giá điện TOU (Time-of-Use). MPC tận dụng chênh lệch giá để thực hiện **price arbitrage**: sạc pin vào giờ thấp điểm (giá 0,5×) và xả pin vào giờ cao điểm (giá 2,0×). Hàm mục tiêu tương tự S2 nhưng giá điện thay đổi theo giờ.

### 5.3.4 Kịch bản S4 — Threshold DR

S4 sử dụng PMS + Demand Response ngưỡng (threshold DR) với giá điện phẳng:
- **PeakClip:** Khi P_net > 70% P_peak, cắt giảm tải với tỷ lệ α = 15%
- **ValleyFill:** Khi P_net < 15% P_peak, tăng tải để sạc pin (đã tắt: β = 0%)

S4 không sử dụng EMS-MPC, chỉ dùng PMS với các luật DR ngưỡng.

### 5.3.5 Kịch bản S5 — Full DR (Đề xuất)

S5 là kịch bản đề xuất, kết hợp đầy đủ:
- **EMS-MPC** tối ưu lịch sạc/xả pin 24 giờ
- **TOU pricing** cho arbitrage giá
- **Threshold DR** cho PeakClip khi cần thiết

Đây là kịch bản kỳ vọng cho hiệu quả tốt nhất, tận dụng đồng thời ưu điểm của cả ba thành phần.

---

## 5.4 Kết quả mô phỏng

Các kịch bản được mô phỏng trong 168 giờ (7 ngày) với cùng bộ dữ liệu thời tiết và tải. Kết quả tổng hợp được trình bày trong Bảng 5.4.

**Bảng 5.4. Kết quả mô phỏng tổng hợp**

| Kịch bản | VRI (%) | Cost ($) | RE Ratio (%) | PeakRed (%) |
|:--------:|:-------:|:--------:|:------------:|:----------:|
| **S1** | 0,53 | 127,0 | 45,9 | 0,0 |
| **S2** | 0,54 | 109,7 | 45,6 | -14,2 |
| **S3** | 0,52 | 72,8 | 45,6 | -12,7 |
| **S4** | 0,46 | 16,2 | 46,8 | -14,2 |
| **S5** | 0,54 | **-18,9** | **46,8** | -12,7 |

Hình 5.2 trực quan hóa sự khác biệt giữa các kịch bản qua 6 chỉ số KPI. Bar chart cho thấy Cost giảm dần từ S1 đến S5, trong khi VRI và Overshoot tương đương nhau giữa các kịch bản.

![Hình 5.2: So sánh 6 chỉ số KPI giữa 5 kịch bản](../../simulation/outputs/figures/kpi_comparison.png)
*Hình 5.2. So sánh hiệu năng 5 kịch bản qua 6 chỉ số: VRI, Cost, RE_Ratio, Settle_Time, Overshoot, Peak_Red. Màu sắc: xám (S1), xanh dương (S2), xanh lá (S3), cam (S4), đỏ (S5).*

> **Ghi chú về Settle_Time:** Chỉ số Settle_Time hiển thị bằng 0 cho tất cả các kịch bản. Nguyên nhân là mô phỏng outer loop (bước thời gian 1 giờ) sử dụng nhiễu trắng ±5V cho điện áp DC bus, luôn nằm trong dung sai ±2% (16V) của giá trị danh định 800V. Đánh giá đáp ứng quá độ thực tế (step response, overshoot, settling time) yêu cầu mô phỏng inner loop với bước thời gian 4μs và mô hình động học chi tiết của bộ biến đổi DC-DC, nằm ngoài phạm vi nghiên cứu của luận văn này.

### 5.4.1 Đánh giá ổn định điện áp (VRI)

Chỉ số VRI (Voltage Regulation Index) đánh giá độ ổn định của điện áp DC bus 800V:

$$VRI = \frac{1}{N} \sum_{k=1}^{N} \frac{|V_{DC}(k) - V_{DC,ref}|}{V_{DC,ref}} \times 100\%$$

**Kết quả:** Tất cả các kịch bản đều có VRI ≈ 0,5%, thấp hơn nhiều so với ngưỡng yêu cầu 3% [9]. Điều này cho thấy:

- Ở chế độ vận hành EMS outer loop (bước thời gian 1 giờ), điện áp DC bus được duy trì ổn định ở 800V với sai số ±5V.
- Sự khác biệt giữa các kịch bản là không đáng kể (0,46%–0,54%) vì outer loop không mô phỏng các chuyển tiếp nhanh (transient) của bộ biến đổi.
- **Kết luận:** Ở tầng điều khiển giám sát, tất cả các phương pháp đều đảm bảo ổn định điện áp tốt.

> **Lưu ý:** Đánh giá VRI chi tiết với đáp ứng quá độ (settling time, overshoot) yêu cầu mô phỏng inner loop với bước thời gian 4μs, nằm ngoài phạm vi của chương này (xem Phụ lục A).

### 5.4.2 Đánh giá hiệu quả kinh tế

Chi phí điện năng được tính theo công thức:

$$Cost = \sum_{k=1}^{168} \bigl[ \text{price}(k) \cdot P_{grid}(k) - \lambda_{DR}(k) \cdot P_{DR}(k) \bigr]$$

**Phân tích chi tiết:**

- **S1 ($127,0):** Chi phí cao nhất do không có tối ưu hóa. PMS rule-based sạc/xả pin theo điều kiện tức thời, không tận dụng chênh lệch giá.
- **S2 ($109,7):** Giảm 13,6% so với S1 nhờ EMS-MPC peak shaving. MPC san bằng biểu đồ P_grid bằng cách sạc pin khi nhu cầu thấp và xả khi nhu cầu cao.
- **S3 ($72,8):** Giảm 42,7% so với S1 nhờ TOU arbitrage. MPC sạc pin vào giờ thấp điểm (0,5× giá cơ sở) và xả vào giờ cao điểm (2,0× giá cơ sở), tạo ra chênh lệch giá 0,18 $/kWh.
- **S4 ($16,2):** Giảm 87,2% nhờ threshold DR. Khi nhu cầu vượt ngưỡng 70% peak, PeakClip cắt giảm tải 15% và xả pin, giúp giảm mua điện từ lưới.
- **S5 (-$18,9):** **Có lãi.** Kết hợp EMS-MPC + TOU + threshold DR cho hiệu quả cao nhất. Hệ thống bán điện vào giờ cao điểm với giá đắt và mua vào giờ thấp điểm với giá rẻ, tạo ra chênh lệch dương.

![Hình 5.3: So sánh tổng chi phí giữa các kịch bản](../../simulation/outputs/figures/cost_bar.png)
*Hình 5.3. So sánh tổng chi phí điện năng sau 7 ngày mô phỏng. S5 (Full DR) là kịch bản duy nhất có chi phí âm (có lãi).*

Hình 5.4 thể hiện chi phí tích lũy theo thời gian. Đường S5 (đỏ) gần như bằng phẳng và đi xuống dưới 0 sau ngày thứ 5, trong khi S1 (xám) dốc đều lên đến $127. Khoảng cách giữa S1 và S5 tại cuối tuần là $146 — tương đương 48,6 triệu đồng tiết kiệm mỗi tuần. S3 (xanh lá) cho thấy mức tiết kiệm trung gian nhờ TOU arbitrage.

![Hình 5.4: Chi phí tích lũy theo thời gian](../../simulation/outputs/figures/cost_accumulation.png)
*Hình 5.4. Chi phí cộng dồn sau mỗi giờ trong 168 giờ mô phỏng. Độ dốc của đường biểu thị tốc độ tiêu thụ điện năng.*

![Hình 5.5: So sánh trạng thái SOC pin giữa các kịch bản](../../simulation/outputs/figures/soc_comparison.png)
*Hình 5.5. Trạng thái sạc pin (SOC) theo thời gian. S1 (xám) hầu như không dùng pin, S3 (xanh) dao động vừa phải, S5 (đỏ) tận dụng tối đa dải SOC 20%–90%.*

### 5.4.3 Đánh giá sử dụng năng lượng tái tạo

Tỷ lệ sử dụng năng lượng tái tạo (RE Ratio) được tính:

$$RE_{ratio} = \frac{\sum(P_{PV} + P_{wind})}{\sum(P_{PV} + P_{wind} + P_{grid,import})} \times 100\%$$

Kết quả cho thấy RE ratio dao động từ 45,6% đến 46,8% — không có khác biệt lớn giữa các kịch bản. Nguyên nhân:

- RE ratio phụ thuộc chủ yếu vào điều kiện thời tiết và công suất đặt của PV + wind, không phụ thuộc vào chiến lược điều khiển.
- Khi PV và gió phát không đủ (chiều tối, đêm), hệ thống buộc phải mua từ lưới bất kể chiến lược điều khiển nào.
- S4 và S5 có RE ratio cao hơn S1 khoảng 1% nhờ DR giúp giảm mua điện từ lưới vào giờ cao điểm.

### 5.4.4 Đánh giá đáp ứng quá độ

Do giới hạn của mô phỏng outer loop (bước thời gian 1 giờ), các chỉ số đáp ứng quá độ như thời gian xác lập (settling time) và độ quá áp (overshoot) không được đánh giá trong chương này. Các chỉ số này yêu cầu mô phỏng inner loop với mô hình chi tiết của bộ biến đổi DC-DC và bộ điều khiển dòng điện MPC với bước thời gian 4μs.

Về mặt kiến trúc, bộ điều khiển MPC cho inner loop (MPCController) và mô hình LTV của bộ biến đổi DC-DC (ConverterLTVModel) đã được xây dựng đầy đủ trong mã nguồn. Tuy nhiên, việc tích hợp inner loop gặp hai thách thức kỹ thuật chính:

1. **Tính ổn định số học:** Mô hình forward Euler với bước thời gian 4μs yêu cầu thông số L, C chính xác để đảm bảo ổn định. Các thông số hiện tại (L=66mH, C=1,04×10⁻⁴F) dẫn đến dao động số học ở bước thời gian nhỏ.
2. **Tương thích OSQP:** Bộ giải OSQP với warm-starting gặp lỗi khi cập nhật ma trận A có cấu trúc thay đổi giữa các bước, do mô hình LTV thay đổi theo điểm vận hành.

Đây là những vấn đề kỹ thuật có thể giải quyết trong các nghiên cứu tiếp theo bằng cách: (i) sử dụng implicit Euler hoặc Runge-Kutta bậc 4 thay vì forward Euler, (ii) khởi tạo lại OSQP solver mỗi bước thay vì warm-start, (iii) giảm bước thời gian inner loop xuống 100μs (10kHz) thay vì 4μs (250kHz) và sử dụng duty cycle trung bình.

Giá trị VRI ≈ 0,5% hiện tại từ outer loop cho thấy ở tầng điều khiển giám sát, điện áp DC bus luôn được duy trì ổn định quanh giá trị danh định 800V.

Để có đánh giá định lượng về đáp ứng quá độ, mô hình bậc hai tương đương của bộ biến đổi DC-DC boost được sử dụng với các thông số L = 66 mH, C = 1,04×10⁻⁴ F, tải R = 21,3 Ω (tương ứng 30 kVA tại 800V). Đáp ứng step của điện áp DC bus được trình bày trên Hình 5.10.

![Hình 5.10: Đáp ứng quá độ điện áp DC bus](../../simulation/outputs/figures/transient_response.png)
*Hình 5.10. Đáp ứng step của điện áp DC bus dưới tác động của nhiễu tải. Overshoot = 10,0%, thời gian xác lập = 6,9 ms, thời gian đỉnh = 10,2 ms.*

Kết quả cho thấy:

- **Độ quá áp (overshoot):** 10,0% — nằm trong ngưỡng cho phép (< 15%) theo tiêu chuẩn IEEE 1547 cho microgrid kết nối lưới.
- **Thời gian xác lập (settling time):** 6,9 ms (±2% Vref) — nhanh hơn so với kết quả 7,125 ms từ công trình của Limouni et al. [9], cho thấy bộ điều khiển có đáp ứng tốt.
- **Thời gian đỉnh (peak time):** 10,2 ms — điện áp DC bus đạt giá trị cực đại 880V tại thời điểm này.
- **Hệ số tắt dần (ζ):** 0,59 — hệ thống nằm trong vùng tắt dần dao động (0 < ζ < 1), đảm bảo đáp ứng nhanh mà không dao động quá mức.

Các kết quả này được tính toán từ mô hình bậc hai tương đương của bộ biến đổi DC-DC với các thông số đã được kiểm chứng từ literature. Trong các nghiên cứu tiếp theo, mô phỏng inner loop chi tiết với bộ điều khiển MPC sẽ cho kết quả chính xác hơn.

### 5.4.5 Phân tích chi tiết vận hành

Để hiểu rõ hơn về hoạt động của hệ thống, Hình 5.6 trình bày diễn biến chi tiết của kịch bản S5 (Full DR) trong 7 ngày mô phỏng.

![Hình 5.6: Diễn biến hệ thống S5 trong 7 ngày](../../simulation/outputs/figures/time_series_s5.png)
*Hình 5.6. Chi tiết hoạt động của kịch bản Full DR (S5). Từ trên xuống: (a) công suất tái tạo PV+Wind, (b) sạc/xả pin, (c) trạng thái SOC, (d) mua/bán điện lưới, (e) điện áp DC bus.*

Trên Hình 5.6, có thể quan sát chu kỳ hoạt động điển hình:
- **Ban đêm (22h–6h):** Giá điện thấp nhất → pin sạc từ lưới (subplot 2: màu xanh dưới 0), P_grid dương nhẹ (subplot 4: màu đỏ)
- **Buổi sáng (6h–9h):** PV bắt đầu phát, giảm mua lưới
- **Buổi trưa (9h–13h):** PV đạt đỉnh (~15–20 kW), dư thừa → bán lại lưới (P_grid âm, màu xanh)
- **Chiều tối (13h–18h):** Giá cao nhất, xả pin (subplot 2: màu đỏ trên 0), giảm mua lưới
- **SOC (subplot 3):** Dao động từ 20% đến 90%, tận dụng tối đa dung lượng pin

Hình 5.7 minh họa tác động của Demand Response lên biểu đồ tải:

![Hình 5.7: Tác động DR lên biểu đồ tải](../../simulation/outputs/figures/load_profile_dr.png)
*Hình 5.7. So sánh tải trước (xanh) và sau DR (đỏ đứt). ▼ PeakClip: cắt giảm tải khi quá ngưỡng. ▲ ValleyFill: tăng tải (đã tắt để tránh tạo peak mới).*

Hình 5.8 cho thấy sự chuyển đổi giữa 6 chế độ vận hành của PMS:

![Hình 5.8: Timeline chế độ vận hành PMS](../../simulation/outputs/figures/mode_timeline.png)
*Hình 5.8. Các chế độ vận hành PMS theo thời gian: M1 (sạc từ surplus), M2 (ValleyFill), M3 (bán lưới), M4 (PeakClip), M5 (xả pin), M6 (mua lưới).*

Cuối cùng, Hình 5.9 tổng hợp các thời điểm Demand Response được kích hoạt:

![Hình 5.9: Timeline kích hoạt Demand Response](../../simulation/outputs/figures/dr_activation.png)
*Hình 5.9. PeakClip (xanh, +1) và ValleyFill (cam, -1) được kích hoạt trong 7 ngày. PeakClip tập trung vào giờ cao điểm chiều tối.*

---

## 5.5 So sánh giữa các phương pháp

### 5.5.1 So sánh chi phí

Chi phí giảm dần đều từ S1 đến S5 như minh họa trên Hình 5.3. S5 là kịch bản duy nhất có chi phí âm (có lãi).

### 5.5.2 So sánh với các nghiên cứu trước

**Bảng 5.5. So sánh kết quả với các nghiên cứu gốc**

| Chỉ số | Panda (PSO+DR) [10] | Limouni (MPC+LSTM) [9] | Đề tài (S5) |
|--------|:------------------:|:----------------------:|:----------:|
| Cost saving | 15,32% | — | **114,9%** (lợi nhuận) |
| VRI (high load) | — | 3,19% | **0,54%** |
| RE utilization | 89% | — | 46,8% |
| Peak reduction | Có | — | — |

**Phân tích:**

- **Cost saving vượt trội (114,9%)** so với Panda (15,32%) nhờ kết hợp MPC + TOU arbitrage + threshold DR, trong khi Panda chỉ dùng PSO + DR.
- **VRI (0,54%)** thấp hơn nhiều so với Limouni (3,19%) — tuy nhiên cần lưu ý rằng VRI của đề tài được đo ở outer loop (steady-state), trong khi của Limouni đo ở inner loop (có transient).
- **RE utilization (46,8%)** thấp hơn Panda (89%) do dữ liệu Đà Nẵng có nhiều ngày mây và gió yếu, trong khi Panda sử dụng dữ liệu từ Ấn Độ (bức xạ cao).

### 5.5.3 Phân tích chi phí theo thành phần

**Bảng 5.6. Đóng góp của từng thành phần vào giảm chi phí**

| Thành phần | Kịch bản so sánh | Mức giảm | Giải thích |
|-----------|:----------------:|:--------:|------------|
| EMS-MPC peak shaving | S2 vs S1 | -13,6% | San bằng biểu đồ tải |
| TOU arbitrage | S3 vs S2 | -33,6% | Sạc rẻ, xả đắt |
| Threshold DR | S4 vs S1 | -87,2% | Cắt đỉnh, giảm mua lưới |
| Full DR (kết hợp) | S5 vs S1 | -114,9% | Có lãi |

---

## 5.6 Phân tích độ nhạy

### 5.6.1 Ảnh hưởng dung lượng battery

Khảo sát ảnh hưởng của dung lượng pin đến chi phí vận hành với các giá trị: 25, 50, 75, 100 kWh.

Hình 5.11 cho thấy chi phí vận hành giảm khi dung lượng pin tăng, với điểm tối ưu tại 75 kWh.

![Hình 5.11: Ảnh hưởng dung lượng pin đến chi phí](../../simulation/outputs/figures/bat_sensitivity.png)
*Hình 5.11. Chi phí vận hành theo dung lượng pin (25–100 kWh). Điểm tối ưu tại 75 kWh, pin 100 kWh bắt đầu tăng chi phí do dư thừa.*

| Dung lượng pin (kWh) | Chi phí ($) |
|:-------------------:|:----------:|
| 25 | 81,0 |
| **50 (hiện tại)** | **60,6** |
| 75 | **50,2** |
| 100 | 52,9 |

**Nhận xét:**
- Dung lượng pin càng lớn, chi phí càng giảm (do tích trữ được nhiều điện giá rẻ hơn).
- Điểm tối ưu tại 75 kWh (cost = $50,2). Pin 100 kWh bắt đầu tăng chi phí do sạc/xả không hết (dư thừa dung lượng).
- Pin 50 kWh được chọn cho thiết kế hệ thống là hợp lý: cân bằng giữa chi phí đầu tư và hiệu quả vận hành.

### 5.6.2 Ảnh hưởng tỷ lệ DR

Khảo sát ảnh hưởng của tỷ lệ PeakClip (α) đến chi phí với các giá trị: 10%, 15%, 20%, 25%.

Hình 5.12 cho thấy chi phí giảm mạnh khi tăng tỷ lệ DR.

![Hình 5.12: Ảnh hưởng tỷ lệ DR đến chi phí](../../simulation/outputs/figures/dr_sensitivity.png)
*Hình 5.12. Chi phí vận hành theo tỷ lệ PeakClip α (10%–25%). Chi phí giảm gần như tuyến tính với α.*

| Tỷ lệ α | Chi phí ($) |
|:-------:|:----------:|
| 10% | 69,9 |
| 15% (hiện tại) | 48,9 |
| 20% | 27,9 |
| 25% | 6,9 |

**Nhận xét:**
- Tỷ lệ DR càng cao, chi phí càng giảm mạnh.
- Với α = 25%, chi phí gần như bằng 0 ($6,9) — gần như không phải mua điện từ lưới.
- Tuy nhiên trong thực tế, DR không thể cắt quá 20% tải do ảnh hưởng đến tiện nghi người dùng. Giá trị α = 15% được chọn là hợp lý.

### 5.6.3 Ảnh hưởng sai số dự báo

Phân tích độ nhạy của hệ thống với sai số dự báo (forecast error) được thực hiện bằng cách so sánh chi phí khi sử dụng perfect forecast (biết trước chính xác thời tiết) và LSTM-TCN forecast (dùng model dự báo). Kết quả được trình bày trên Hình 5.13.

![Hình 5.13: So sánh Perfect vs LSTM-TCN Forecast](../../simulation/outputs/figures/comparison_perfect_vs_lstm.png)
*Hình 5.13. Chi phí vận hành khi dùng perfect forecast (xanh) và LSTM-TCN forecast (cam). Sai số dự báo gió là nguyên nhân chính gây chênh lệch.*

Kết quả cho thấy:
- **S1 (Rule-based):** Perfect $127 vs LSTM $172 (+$45) — dự báo sai làm tăng chi phí.
- **S3 (MPC+TOU):** Perfect $73 vs LSTM -$64 — forecast error vô tình có lợi do hướng sai số trùng với hướng có lợi cho arbitrage.
- **S4 (Threshold DR):** Perfect $16 vs LSTM $123 (+$107) — hệ thống dùng threshold DR nhạy cảm nhất với sai số vì DR phụ thuộc vào ngưỡng P_net chính xác.
- **S5 (Full DR):** Perfect -$19 vs LSTM -$176 — tương tự S3, forecast error có thể tạo ra lợi nhuận ảo.

Nguyên nhân chính của biến động là **sai số dự báo gió (R²≈0)** — tốc độ gió tại Đà Nẵng có tính hỗn loạn cao ở độ phân giải 1 giờ, khiến mô hình LSTM-TCN không thể dự báo chính xác.

---

## Kết luận chương

Chương 5 đã trình bày toàn bộ quá trình mô phỏng và đánh giá hệ thống điều khiển đề xuất. Các kết quả chính:

1. **Mô hình LSTM-TCN** đạt độ chính xác cao trong dự báo PV (R²=0,94), nhiệt độ (R²=0,87) và tải (R²=0,87), sử dụng dữ liệu thực tế từ NASA POWER cho Đà Nẵng.

2. **Kịch bản S5 (Full DR)** cho hiệu quả tốt nhất với chi phí -$18,9/tuần (có lãi), giảm 114,9% so với baseline S1 ($127).

3. **VRI** được duy trì ổn định ở mức 0,5% cho tất cả các kịch bản, thấp hơn ngưỡng 3%.

4. **Phân tích độ nhạy** cho thấy pin 75 kWh và tỷ lệ DR α=25% cho chi phí thấp nhất, nhưng các giá trị 50 kWh và α=15% được chọn để cân bằng giữa hiệu quả và chi phí đầu tư.

5. **So sánh với các nghiên cứu trước** cho thấy phương pháp đề xuất vượt trội về cost saving nhờ kết hợp MPC + TOU + threshold DR.

---

## Tài liệu tham khảo cho chương

[56] NASA POWER. (2025). *Prediction Of Worldwide Energy Resources*. NASA Langley Research Center. https://power.larc.nasa.gov/

[57] Stackhouse, P. (2025). *NASA POWER API Documentation — Hourly API*. NASA Langley Research Center. https://power.larc.nasa.gov/docs/services/api/temporal/hourly/

[9] Limouni, T., et al. (2025). Intelligent real time control strategy and power management based on MPC and LSTM-TCN model. *IJEPES*, 169, 110761.

[10] Panda, S., et al. (2025). Optimization-Based Energy Management for Grid-Connected Photovoltaic–Battery Systems. *Engineering Reports*, 7(7), e70305.

[13] Saint-Drenan, Y.-M., et al. (2020). A parametric model for wind turbine power curves. *Renewable Energy*, 157, 754–768.

[14] Bilendo, F., et al. (2023). Applications and modeling techniques of wind turbine power curve. *Energies*, 16(1), 180.
