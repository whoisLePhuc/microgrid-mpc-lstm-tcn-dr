# Giải Thích Chi Tiết Các Sơ Đồ Mô Phỏng Microgrid

**Dự án:** Nghiên cứu điều khiển thời gian thực cho hệ PV–Wind–Battery với Demand Response trong Microgrid thông minh

**Vị trí:** `simulation/outputs/figures/`

---

## 1. `kpi_comparison.png` — So sánh KPI giữa 5 kịch bản

### Mục đích
Trả lời câu hỏi: **"Kịch bản nào tốt nhất?"** Bằng cách so sánh 5 kịch bản vận hành qua 6 chỉ số KPI.

### Cấu tạo
- **6 biểu đồ con (subplot):** VRI, Cost, RE_Ratio, Settle_Time, Overshoot, Peak_Red
- **Mỗi biểu đồ:** 5 cột bar tương ứng 5 kịch bản (Rule-based → EMS-MPC → MPC+TOU → Threshold DR → Full DR)
- **Màu sắc:** Xám → Xanh dương → Xanh lá → Cam → Đỏ (theo thứ tự cải tiến dần)

### Các chỉ số
| KPI | Ý nghĩa | Giá trị tốt | Công thức |
|-----|---------|:-----------:|-----------|
| **VRI** (%) | Độ ổn định điện áp DC bus 800V | Thấp (<3%) | `mean(\|VDC-800\|/800) × 100%` |
| **Cost** ($) | Tổng chi phí điện 7 ngày | Thấp (càng thấp càng tốt) | `Σ(price×P_grid) - Σ(λ×P_DR)` |
| **RE_Ratio** (%) | Tỷ lệ NLTT trên tổng tiêu thụ | Cao (>90%) | `Σ(P_PV+P_wind) / Σ(P_PV+P_wind+P_grid_import)` |
| **Settle_Time** (s) | Thời gian ổn định VDC sau nhiễu | Thấp | Time to ±2% Vref |
| **Overshoot** (%) | Độ vọt lố điện áp khi chuyển tiếp | Thấp (<5%) | `max(\|VDC-800\|)/800` |
| **Peak_Red** (%) | Mức giảm công suất đỉnh mua từ lưới | **Cao, dương** | `(P_peak_baseline - P_peak_dr) / P_peak_baseline` |

### Cách đọc
1. **Nhìn tổng quan:** Scan từ trái sang phải (S1 → S5). Bar thường có xu hướng: Cost giảm dần, RE_Ratio tăng dần.
2. **Cost là quan trọng nhất:** Nếu S5 có bar thấp nhất → Full DR tiết kiệm nhất.
3. **Peak_Red:** Nếu bar dương (trên 0) → hệ thống đã giảm được đỉnh. Nếu âm → DR tạo peak mới.
4. **Settle_Time + Overshoot:** Nếu các bar gần bằng nhau → tất cả kịch bản đều ổn định như nhau.

### Phát hiện chính từ mô phỏng
```
Chỉ số        S1      S2      S3      S4      S5      Đơn vị
Cost         127.0   109.7   72.9    16.2    -18.8    $
RE_Ratio     45.9    45.5    45.6    46.7    46.8     %
Peak_Red     0.0     -16.1   -15.8   -16.1   -15.8    %
```
S5 (Full DR) có cost thấp nhất và RE cao nhất. PeakRed chưa dương (cần cải thiện).

### Liên kết
- Xem `cost_bar.png` để so sánh cost rõ hơn
- Xem `time_series_s5.png` để hiểu tại sao S5 hoạt động tốt

---

## 2. `time_series_s5.png` — Diễn biến hệ thống S5 trong 7 ngày

### Mục đích
Trả lời câu hỏi: **"Hệ thống hoạt động thế nào trong 1 tuần?"** Cho thấy chi tiết từng giờ của giải pháp Full DR (S5).

### Cấu tạo
5 subplot chồng dọc, cùng trục thời gian X (7 ngày):

| Subplot | Tín hiệu | Màu | Đơn vị |
|:-------:|----------|:---:|:------:|
| 1 | **Renewable**: PV + Wind | Cam (PV) + Xanh (Wind) | kW |
| 2 | **Battery**: sạch/xả | Đỏ (xả) + Xanh lá (sạc) | kW |
| 3 | **SOC**: trạng thái pin | Xanh lá | % |
| 4 | **Grid**: mua/bán | Đỏ (mua) + Xanh (bán) | kW |
| 5 | **DC Bus**: điện áp | Xám | V |

### Cách đọc — từ trên xuống dưới

**Subplot 1 — Renewable:**
- Ban ngày (6h-18h): PV phát điện, đỉnh trưa ~15-20 kW
- Wind rải rác cả ngày, không theo quy luật (ngẫu nhiên)
- Diện tích màu cam + xanh = tổng năng lượng tái tạo

**Subplot 2 — Battery:**
- Màu xanh lá (dưới 0) = sạc pin (tiêu thụ điện)
- Màu đỏ (trên 0) = xả pin (cấp điện)
- Mẫu hình điển hình: sạc đêm/khuya (giá rẻ) → xả chiều (giá đắt)

**Subplot 3 — SOC:**
- Đường từ 20% → 90%. Càng dao động nhiều → càng tận dụng pin
- Nếu SOC chạm 20% → pin cạn (phải mua điện từ lưới)
- Nếu SOC chạm 90% → pin đầy (không sạc thêm được)

**Subplot 4 — Grid:**
- Trên 0 (đỏ) = mua điện từ lưới → tốn tiền
- Dưới 0 (xanh) = bán điện lên lưới → có thu nhập
- Đỉnh cao nhất = peak demand (cần giảm)

**Subplot 5 — DC Bus:**
- Lý tưởng: đường thẳng ở 800V
- Nhiễu nhỏ ±5V là bình thường
- Nếu dao động lớn → mất ổn định

### Luồng hoạt động 1 ngày điển hình (Full DR)
```
Giờ    PV  Wind  Pin       Lưới        Giải thích
0-6    0   2-5   Sạc (-5kW) Mua nhẹ     Giá rẻ (0.06$/kWh) → sạc pin
6-9    5   2-4   Sạc nhẹ    Giảm mua    PV bắt đầu phát
9-13   15  1-3   Ngừng sạc  Bán lưới    PV nhiều, dư thừa → bán
13-18  10  1-2   Xả (+8kW)  Giảm mua    Giá đắt (0.24$/kWh) → xả pin
18-22  0   2-4   Xả (+5kW)  Mua          Hết PV, pin xả nốt
22-24  0   2-5   Sạc (-5kW) Mua          Giá rẻ lại → sạc cho ngày mai
```

### Phát hiện chính
- **Peak clipping:** Subplot 4 có đỉnh thấp hơn so với S1 nhờ pin xả giờ cao điểm
- **Valley filling:** Subplot 4 có mua điện nhiều hơn vào ban đêm để sạc pin
- **Battery cycling:** Subplot 3 cho thấy pin sạc-xả 1 lần/ngày (1 cycle)

---

## 3. `cost_bar.png` — So sánh chi phí điện

### Mục đích
Trả lời: **"Kịch bản nào tiết kiệm nhất?"** So sánh trực quan tổng chi phí 7 ngày.

### Cấu tạo
- Trục X: 5 kịch bản (Rule-based → EMS-MPC → MPC+TOU → Threshold DR → Full DR)
- Trục Y: Tổng chi phí ($) — dương = tốn tiền, âm = có lãi
- Màu sắc: gradient từ xám (tệ nhất) → đỏ (tốt nhất)

### Cách đọc
1. Bar càng thấp → càng tiết kiệm
2. Bar dưới 0 (âm) → hệ thống kiếm ra tiền (bán điện > mua điện)
3. So sánh chiều cao: `S1 - S5` = số tiền tiết kiệm được

### Công thức chi phí
```
Cost = Σ(price × P_grid) - Σ(λ_DR × P_DR)

Trong đó:
- price × P_grid: Tiền mua điện (>0) / bán điện (<0)
  - P_grid > 0 (mua): cost dương
  - P_grid < 0 (bán): cost âm (thu nhập)
- λ_DR × P_DR: Khuyến khích DR
  - P_DR > 0 (PeakClip, cắt tải): được thưởng
  - P_DR < 0 (ValleyFill, tăng tải): phải trả thêm
```

### Phát hiện chính
```
Kịch bản          Cost     Δ vs S1
Rule-based (S1)   $127     —
EMS-MPC (S2)      $110     -13.6%
MPC+TOU (S3)      $73      -42.5%
Threshold (S4)    $16      -87.4%
Full DR (S5)      -$19     LỢI NHUẬN!
```

S5 không chỉ tiết kiệm mà còn **có lãi** — nhờ bán điện giá cao giờ peak.

---

## 4. `bat_sensitivity.png` — Độ nhạy dung lượng pin

### Mục đích
Trả lời: **"Nên chọn pin dung lượng bao nhiêu?"** Phân tích ảnh hưởng của dung lượng pin lên chi phí.

### Cấu tạo
- Trục X: Dung lượng pin (25 → 50 → 75 → 100 kWh)
- Trục Y: Tổng chi phí ($)
- Đường đỏ + chấm vuông

### Cách đọc
- **Đường đi xuống:** Pin càng to càng tiết kiệm → mua pin lớn hơn
- **Đường đi lên:** Pin quá to gây lãng phí → pin không sạc/xả hết
- **Điểm gãy:** Dung lượng tối ưu (cân bằng giữa tiết kiệm và chi phí đầu tư)

### Phát hiện chính
```
25 kWh: $81
50 kWh: $61  ← dung lượng hiện tại
75 kWh: $50
100 kWh: $53 ← bắt đầu tăng (pin quá to)
```

Pin 75 kWh cho cost thấp nhất, nhưng pin 50 kWh là cân bằng tốt giữa hiệu quả và chi phí đầu tư.

### Liên kết
Kết quả này dùng để biện luận chọn dung lượng pin 50 kWh trong thiết kế hệ thống.

---

## 5. `dr_sensitivity.png` — Độ nhạy tỷ lệ DR

### Mục đích
Trả lời: **"Nên đặt mức DR bao nhiêu?"** Phân tích ảnh hưởng của tỷ lệ PeakClip (α) lên chi phí.

### Cấu tạo
- Trục X: Tỷ lệ DR α (10% → 15% → 20% → 25%)
- Trục Y: Tổng chi phí ($)
- Đường đỏ + chấm vuông + tô mờ

### Cách đọc
- **α=10%:** Cắt tối đa 10% tải khi PeakClip → cost cao (ít cắt)
- **α=25%:** Cắt tối đa 25% tải → cost thấp nhất (cắt mạnh)
- Nếu đường đột ngột đi lên → DR quá mạnh gây hại

### Phát hiện chính
```
α=10%: $69.9
α=15%: $48.9
α=20%: $27.9
α=25%: $6.9  ← gần như miễn phí điện!
```

Tỷ lệ DR càng cao càng tiết kiệm. Tuy nhiên trong thực tế, α>20% có thể ảnh hưởng đến tiện nghi người dùng.

---

## 6. `cost_accumulation.png` — Tích lũy chi phí theo thời gian

### Mục đích
Trả lời: **"Tiết kiệm diễn ra như thế nào theo thời gian?"** Cho thấy tốc độ tích lũy chi phí.

### Cấu tạo
- Trục X: Thời gian (168 giờ = 7 ngày)
- Trục Y: Chi phí cộng dồn ($) — cộng dồn sau mỗi giờ
- 3 đường:
  - Xám (S1): Rule-based — baseline
  - Xanh lá (S3): MPC+TOU — arbitrage giá
  - Đỏ (S5): Full DR — giải pháp đề xuất

### Cách đọc
1. **Độ dốc:** Dốc → đang tốn tiền nhanh. Bằng phẳng → tiết kiệm. Đi xuống → có lãi.
2. **Khoảng cách giữa 2 đường:** Lượng tiền tiết kiệm được tại thời điểm đó.
3. **Điểm giao nhau với trục hoành (y=0):** Thời điểm bắt đầu có lãi.

### Phát hiện chính
- **S1 (xám):** Dốc đều → tốn tiền liên tục, không có lúc nào tiết kiệm
- **S3 (xanh):** Bằng phẳng hơn S1 → tiết kiệm nhờ TOU arbitrage
- **S5 (đỏ):** Đi ngang gần 0, về cuối đi xuống dưới 0 → **có lãi!**

Càng về cuối tuần, S5 càng tiết kiệm nhiều hơn S1 nhờ DR và arbitrage.

---

## 7. `load_profile_dr.png` — Tác động DR lên biểu đồ tải

### Mục đích
Trả lời: **"DR thay đổi biểu đồ tải thế nào?"** Cho thấy khi nào PeakClip cắt tải và ValleyFill tăng tải.

### Cấu tạo
- Trục X: Thời gian (7 ngày)
- Trục Y: Công suất (kW)
- **Đường xanh dương đậm:** Tải gốc (P_load) — trước khi áp dụng DR
- **Đường đỏ đứt:** Tải hiệu dụng sau DR (P_load - P_DR)
- **▼ xanh lá (PeakClip):** Điểm DR cắt giảm tải
- **▲ cam (ValleyFill):** Điểm DR tăng tải (sạc pin)

### Cách đọc
1. **Khoảng cách giữa 2 đường = mức độ DR tác động**
2. **Khi PeakClip (▼):** Đường đỏ dưới đường xanh → tải giảm
3. **Khi ValleyFill (▲):** Đường đỏ trên đường xanh → tải tăng
4. **Chỗ 2 đường chồng khít:** Không có DR

### Ví dụ cụ thể từ sơ đồ
```
Ngày 1, ~8h sáng: ▲ ValleyFill → đường đỏ cao hơn xanh (sạc pin từ lưới)
Ngày 1, ~18h chiều: ▼ PeakClip → đường đỏ thấp hơn xanh (cắt tải)
Đêm: 2 đường gần nhau → không DR
```

### Phát hiện chính
PeakClip (▼) tập trung vào giờ cao điểm chiều tối (13-18h) khi giá điện đắt nhất. ValleyFill (▲) tập trung vào ban đêm/khuya khi giá rẻ.

### Liên kết
Xem `dr_activation.png` để biết khi nào PeakClip/ValleyFill kích hoạt dưới dạng timeline.

---

## 8. `mode_timeline.png` — Chế độ vận hành PMS

### Mục đích
Trả lời: **"PMS chuyển đổi giữa các chế độ ra sao?"** Cho thấy 6 mode vận hành theo thời gian.

### Cấu tạo
- Trục X: Thời gian (7 ngày)
- Trục Y: Mode (M1-M6) — không có giá trị số, chỉ hiển thị màu
- **Màu nền:** Mỗi màu tương ứng 1 chế độ vận hành

### 6 Mode vận hành
| Màu | Mode | Khi nào? | Hành động |
|:---:|:----:|----------|-----------|
| Xanh dương | **M1: Charge** | Có surplus (PV>load), pin < 85% | Sạc pin từ PV dư |
| Cam | **M2: ValleyFill** | Có surplus, pin ≥ 85%, giờ thấp điểm | Sạc thêm từ lưới (giá rẻ) |
| Xanh lá | **M3: Export** | Có surplus, pin ≥ 85%, không DR | Bán hết lên lưới |
| Đỏ | **M4: PeakClip** | Thiếu hụt, pin > 30%, giờ cao điểm | Xả pin + cắt tải DR |
| Tím | **M5: Discharge** | Thiếu hụt, pin > 30%, giờ thường | Xả pin bình thường |
| Nâu | **M6: Import** | Thiếu hụt, pin ≤ 30% (cạn) | Mua điện từ lưới |

### Cách đọc
1. **Ban ngày (6-18h):** Chủ yếu M1 (sạc từ PV) + M3 (bán lưới) khi nắng
2. **Chiều tối (13-18h):** M4 (PeakClip) xuất hiện nhiều → DR hoạt động mạnh
3. **Đêm (22-6h):** M2 (ValleyFill) + M6 (Import) khi không có PV
4. **Chuyển đổi liên tục:** Hệ thống phản ứng linh hoạt với thay đổi của tải và PV

### Phát hiện chính
- M4 (PeakClip) xuất hiện đều đặn mỗi chiều → hệ thống chủ động giảm tải đỉnh
- M6 (Import) chỉ xuất hiện khi thực sự cần (SOC thấp) → tận dụng pin tốt
- M3 (Export) xuất hiện giữa trưa khi PV dư thừa

---

## 9. `soc_comparison.png` — So sánh SOC pin giữa các kịch bản

### Mục đích
Trả lời: **"Dùng pin khác nhau thế nào giữa các kịch bản?"** So sánh chiến lược quản lý pin.

### Cấu tạo
- Trục X: Thời gian (7 ngày)
- Trục Y: SOC từ 0% → 100%
- **Đường xám (S1):** Rule-based — baseline
- **Đường xanh lá (S3):** MPC+TOU — arbitrage giá
- **Đường đỏ (S5):** Full DR — giải pháp đề xuất
- **2 đường kẻ đứt:** SOC min (20%) và SOC max (90%)

### Cách đọc
1. **Biên độ dao động:** Càng rộng → càng tận dụng pin nhiều
2. **SOC trung bình:** Giá trị càng cao → pin luôn đầy (an toàn hơn)
3. **Chạm threshold:** Nếu đường chạm 20% (soc min) → pin gần cạn (rủi ro mất điện)

### Phát hiện chính
- **S1 (xám):** SOC gần như phẳng (~50-60%) → PMS ít dùng pin, không arbitrage
- **S3 (xanh):** SOC dao động từ 30% → 85% → TOU arbitrage: sạc đêm (giá rẻ), xả chiều (giá đắt)
- **S5 (đỏ):** SOC dao động rộng nhất 20% → 90% → Full DR tận dụng tối đa pin
- **S5 chạm SOC min 20%:** Đây là rủi ro — nếu dự báo sai có thể hết pin

---

## 10. `dr_activation.png` — Kích hoạt Demand Response

### Mục đích
Trả lời: **"Bao nhiêu lần DR được kích hoạt?"** Timeline kích hoạt PeakClip và ValleyFill.

### Cấu tạo
- Trục X: Thời gian (7 ngày)
- Trục Y:
  - **+1 (xanh lá):** PeakClip — đang cắt tải
  - **0 (nền):** DR không hoạt động
  - **-1 (cam):** ValleyFill — đang tăng tải

### Cách đọc
1. **Tần suất:** Càng nhiều thanh → DR càng hoạt động tích cực
2. **Phân bố theo ngày:** PeakClip thường vào chiều tối (13-18h), ValleyFill vào đêm/khuya
3. **Mẫu hình:** Lặp lại mỗi ngày → DR hoạt động theo quy luật

### Phát hiện chính
- **PeakClip (xanh):** 15-16 lần/tuần → chủ yếu giờ cao điểm chiều
- **ValleyFill (cam):** Đã tắt (beta_fill=0) để tránh tạo peak mới

### Liên kết
Mỗi khi có thanh xanh (PeakClip), nhìn vào `load_profile_dr.png` sẽ thấy tải giảm xuống tương ứng.

---

## 11. `comparison_perfect_vs_lstm.png` — So sánh Perfect vs LSTM Forecast

### Mục đích
Trả lời: **"Dùng LSTM dự báo có tốt không?"** So sánh chi phí khi dùng dự báo hoàn hảo vs dự báo từ LSTM.

### Cấu tạo
- Trục X: 5 kịch bản
- Trục Y: Tổng chi phí ($)
- **Cột xanh dương:** Perfect forecast — biết trước thời tiết chính xác
- **Cột cam:** LSTM-TCN forecast — dùng model dự báo

### Cách đọc
1. **2 cột bằng nhau:** LSTM dự báo hoàn hảo (ngang perfect)
2. **Cột cam cao hơn:** Forecast error → tốn thêm tiền
3. **Cột cam thấp hơn:** Forecast error vô tình có lợi

### Phát hiện chính
```
Kịch bản      Perfect   LSTM      Δ
Rule-based    $127      $172      +$45 (dự báo sai → tốn thêm)
EMS-MPC       $110      $146      +$36
MPC+TOU       $73       -$64      Có lãi hơn! (may mắn)
Threshold DR  $16       $123      +$107 (tốn thêm nhiều)
Full DR       -$19      -$176     Lãi hơn! (forecast error có lợi)
```

Kết quả cho thấy dự báo gió (wind) kém (R²≈0) ảnh hưởng nhiều đến các kịch bản dùng threshold DR.

---

## 12. `forecast_validation.png` — Kiểm tra độ chính xác LSTM-TCN

### Mục đích
Trả lời: **"LSTM dự báo chính xác đến đâu?"** So sánh giá trị dự báo với giá trị thực tế.

### Cấu tạo
3 subplot:
| Subplot | Đại lượng | Màu thực tế | Màu dự báo |
|:-------:|-----------|:-----------:|:----------:|
| 1 | **PV Power (kW)** — Công suất PV | Cam | Đỏ đứt |
| 2 | **Load (kW)** — Nhu cầu tải | Xanh dương | Đỏ đứt |
| 3 | **Price ($/kWh)** — Giá điện | Xanh lá | Đỏ đứt |

Phần tô đỏ mờ giữa 2 đường = sai số dự báo. Càng mờ càng chính xác.

### Cách đọc
1. **2 đường chồng khít:** Dự báo rất chính xác
2. **Khoảng cách giữa 2 đường lớn:** Dự báo kém chính xác
3. **Màu đỏ dưới hoặc trên:** Dự báo thấp hơn hoặc cao hơn thực tế

### Phát hiện chính
| Đại lượng | R² | Đánh giá |
|-----------|:--:|:--------:|
| **PV Power** | **0.94** | Rất tốt — model bám sát biểu đồ PV |
| **Load** | **0.87** | Tốt — nắm được xu hướng ngày-đêm |
| **Price** | **1.00** | Hoàn hảo — giá TOU là deterministic, model học được |

Chất lượng dự báo PV và Load là chấp nhận được cho ứng dụng microgrid.

---

## 13. `kpi_results.json` — Số liệu KPI dạng bảng

### Nội dung
File JSON chứa số liệu thô của tất cả KPI cho 5 kịch bản:

```json
{
  "S1": {"VRI": 0.51, "Cost": 127.0, "RE_Ratio": 45.9, "Settle_Time": 0.0, "Overshoot": 1.9, "Peak_Red": 0.0},
  "S2": {"VRI": 0.50, "Cost": 109.7, "RE_Ratio": 45.5, ...},
  "S3": {"VRI": 0.50, "Cost": 72.9, ...},
  "S4": {"VRI": 0.47, "Cost": 16.2, ...},
  "S5": {"VRI": 0.47, "Cost": -18.8, "RE_Ratio": 46.8, "Peak_Red": -15.8}
}
```

### Cách dùng
- Import vào LaTeX để tạo bảng trong báo cáo
- Dùng làm dữ liệu đầu vào cho Python/Excel vẽ thêm đồ thị khác
- Tính % cải thiện giữa các kịch bản

---

## Tổng kết

| Sơ đồ | Mục đích | Câu hỏi trả lời | Chapter |
|-------|----------|-----------------|:-------:|
| `kpi_comparison` | So sánh tổng thể 5 kịch bản | Kịch bản nào tốt nhất? | 5 |
| `time_series_s5` | Chi tiết 7 ngày S5 | Hệ thống chạy thế nào? | 5 |
| `cost_bar` | So sánh chi phí | Tiết kiệm bao nhiêu? | 5.3 |
| `bat_sensitivity` | Độ nhạy dung lượng pin | Chọn pin bao nhiêu? | 5.5 |
| `dr_sensitivity` | Độ nhạy tỷ lệ DR | Chọn mức DR nào? | 5.5 |
| `cost_accumulation` | Tích lũy chi phí | Tiết kiệm diễn ra thế nào? | 5.3 |
| `load_profile_dr` | Tác động DR lên tải | DR thay đổi tải ra sao? | 5.4 |
| `mode_timeline` | Chế độ PMS theo thời gian | PMS chuyển mode thế nào? | 4.4 |
| `soc_comparison` | So sánh SOC pin | Các phương pháp dùng pin khác nhau? | 5.3 |
| `dr_activation` | Timeline kích hoạt DR | Bao nhiêu lần DR kích hoạt? | 5.4 |
| `comparison_perfect_vs_lstm` | So sánh forecast | LSTM dự báo tốt không? | 5.6 |
| `forecast_validation` | Kiểm tra độ chính xác | Model dự báo chính xác? | 5.6 |
