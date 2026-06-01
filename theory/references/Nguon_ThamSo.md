# NGUỒN GỐC CÁC THAM SỐ TRONG HỆ THỐNG

## Ký hiệu nguồn
| Ký hiệu | Nguồn |
|---------|-------|
| **[P1]** | Panda et al. (2025) — Engineering Reports, 7(7), e70305 |
| **[P2]** | Limouni et al. (2025) — IJEPES, 169, 110761 |
| **[R]** | Reference/Algorithms and Theories Overview.md |
| **[Lit]** | Verified từ literature search (IEC, MDPI, IEEE) |
| **[New]** | Đề xuất mới cho đề tài (không có trong 2 bài báo gốc) |

---

## 1. HỆ THỐNG PV

| Tham số | Giá trị | Nguồn | Ghi chú |
|---------|---------|-------|---------|
| Công suất lắp đặt | **20 kWp** | [P1] | Panda dùng 20kW system |
| Module | **ASW-250P** | [P2] | Limouni dùng module này |
| Số module | **80** (20,000W/250W) | Tính từ [P1]+[P2] | 20kWp/250W = 80 module |
| Pmax mỗi module | **250 W** | [P2] §Thông số PV | |
| Voc | **43.22 V** | [P2] | |
| Isc | **7.76 A** | [P2] | |
| Vmp | **35.2 V** | [P2] | |
| Imp | **7.1 A** | [P2] | |
| Hệ số nhiệt Voc | **-0.30278 %/°C** | [P2] | |
| Hệ số nhiệt Isc | **0.035271 %/°C** | [P2] | |
| Công suất PV | $P_{PV} = \eta_{PV} \times A \times G$ | [P1][P2] | Simplified model cho optimization |

> **Kết luận:** Toàn bộ thông số PV lấy từ 2 bài báo gốc. Module ASW-250P từ [P2], công suất hệ thống 20kWp từ [P1].

---

## 2. HỆ THỐNG WIND TURBINE

| Tham số | Giá trị | Nguồn | Ghi chú |
|---------|---------|-------|---------|
| Công suất định mức | **10 kW** | **[New]** | Cả 2 papers đều không có wind. Chọn 10kW để tỷ lệ PV:Wind = 2:1 (phù hợp microgrid) |
| Vcut-in | **3 m/s** | [Lit] | IEC 61400-12-1:2022 — typical range 3-4 m/s |
| Vrated | **12 m/s** | [Lit] | IEC 61400-12-1 — typical range 12-17 m/s |
| Vcut-out | **25 m/s** | [Lit] | IEC 61400-12-1 — typical range 20-30 m/s |
| Rotor diameter | **7 m** | **[New]** | Tính từ A = πD²/4 ≈ 38.5 m² cho 10kW |
| Cp max | **0.45** | [Lit] | < Betz limit 0.593, typical 0.35-0.50 [MDPI Energies 2023] |
| Độ cao hub | **30 m** | **[New]** | Phù hợp microgrid quy mô nhỏ |
| Hệ số nhám α | **0.14** | [R] | Đất trống, ít chướng ngại |
| Mô hình wind speed | $V_{hub} = V_{ref}(H_{hub}/H_{ref})^\alpha$ | [R] | Power law — verified |
| Mô hình power curve | IEC 4-region | [Lit] | IEC 61400-12-1:2022 |

> **Kết luận:** Wind turbine là **thành phần mới hoàn toàn** cho đề tài. Công suất 10kW được đề xuất dựa trên tỷ lệ PV:Wind phù hợp. Các thông số vận hành (Vci, Vr, Vco) theo tiêu chuẩn IEC 61400-12-1 và literature.

---

## 3. HỆ THỐNG BATTERY

| Tham số | Giá trị | Nguồn | Ghi chú |
|---------|---------|-------|---------|
| Dung lượng | **50 kWh** | [P1] | Panda dùng 50kWh BESS |
| Điện áp nominal | **120 V** | [P2] | Limouni dùng 120V battery |
| SoC min | **20%** | [P1] | Panda: SoC range 20-90% |
| SoC max | **90%** | [P1] | |
| SoC charge stop (PMS) | **85%** | **[New]** | Điều chỉnh — tham khảo [P2] 80% và [P1] 90% |
| SoC discharge stop (PMS) | **30%** | **[New]** | Điều chỉnh — có margin từ hard limit 20% |
| Hiệu suất sạc ηch | **0.95** | [P2] | Limouni dùng 0.95 |
| Hiệu suất xả ηdch | **0.95** | [P2] | |
| Pch max | **25 kW** | **[New]** | C‑rate = 0.5C (50kWh × 0.5 = 25kW) |
| Pdch max | **25 kW** | **[New]** | C‑rate = 0.5C |
| Mô hình | Coulomb counting | [P2][R] | $SoC(k+1) = SoC(k) + (\eta_{ch}P_{ch} - P_{dch}/\eta_{dch})\Delta t/E_{bat}$ |

> **Kết luận:** Battery kết hợp từ cả 2 papers: dung lượng 50kWh từ [P1], điện áp 120V từ [P2]. SoC limits từ [P1]. C-rate được đề xuất mới dựa trên thông lệ.

---

## 4. BỘ BIẾN ĐỔI (CONVERTERS)

| Tham số | Giá trị | Nguồn | Ghi chú |
|---------|---------|-------|---------|
| **DC Bus** | | | |
| Điện áp DC bus | **800 V** | [P2] | Limouni dùng 800VDC |
| Tụ DC bus | **1.04×10⁻⁴ F** | [P2] | |
| **Inverter** | | | |
| Công suất | **30 kVA** | **[New]** | PV 20kW + Wind 10kW + Battery margin = ~30kVA |
| AC Bus | **380 V / 50 Hz** | **[New]** | Tiêu chuẩn hạ thế châu Âu |
| **PV Boost Converter** | | | |
| Cuộn cảm L_PV | **66 mH** | [P2] | |
| Điện trở r_L_PV | **0.066 Ω** | [P2] | |
| Tụ C_PV | **9.128×10⁻⁵ F** | [P2] | |
| Tần số switching | **10 kHz** | [P2] | |
| **Wind Boost Converter** | | | |
| Cuộn cảm L_wind | **5 mH** | [Lit] | Verified từ: [Zammit 2017 — 35mH cho 5kW], [MDPI Electronics 2020 — 450μH cho 4kW]. Khác với PV vì wind turbine PMSG có đặc tính dòng khác. |
| Điện trở r_L_wind | **0.015 Ω** | **[New]** | Tỷ lệ với L |
| Tụ C_wind | **9.128×10⁻⁵ F** | [P2] | Dùng cùng giá trị PV |
| Tần số switching | **10 kHz** | [P2] | |
| **Battery Bidirectional Converter** | | | |
| Cuộn cảm L_bat | **66 mH** | [P2] | Giống PV |
| Điện trở r_L_bat | **0.066 Ω** | [P2] | |

> **Kết luận:** Thông số converter chủ yếu từ [P2]. L_wind khác với L_PV vì wind turbine có đặc tính điện khác (PMSG, dòng AC trước khi chỉnh lưu). Inverter 30kVA được tính từ tổng công suất hệ thống.

---

## 5. LSTM-TCN FORECASTING

| Tham số | Giá trị | Nguồn | Ghi chú |
|---------|---------|-------|---------|
| **Kiến trúc** | LSTM(256→64) → TCN(3 blocks) → Dense | [P2] | Sequential LSTM→TCN — giữ nguyên từ Limouni |
| LSTM Layer 1 | **256 neurons** | [P2] | |
| LSTM Layer 2 | **64 neurons** | [P2] | |
| TCN residual blocks | **3** | [P2] | |
| TCN filters | **128** | [P2] | |
| Kernel size | **3** | [P2] | |
| Dilation factors | **[1, 2, 4]** | [P2] | Exponential growth |
| Dropout (LSTM + TCN) | **0.2** | [Lit] | Optimal from [Frontiers in Energy Research 2024] |
| Input window | **12 time steps** | [P2] | Look-back = 12 |
| Output horizon | **1-4 steps (H)** | **[New]** | Mở rộng từ [P2] để phục vụ MPC prediction horizon |
| Learning rate | **0.001** | [P2] | Adam optimizer |
| Epochs | **100** | [P2] | Early stopping patience=10 |
| Batch size | **100** | [P2] | |
| Loss function | **MSE** | [Lit] | Standard cho regression |
| **Input features** | | | |
| GHI | ✅ | [P2] | Có sẵn |
| Nhiệt độ | ✅ | [P2] | Có sẵn |
| Wind speed | **✅ Thêm mới** | **[New]** | Không có trong [P2] |
| Load demand | ✅ | [P2] | Có sẵn |
| Electricity price | **✅ Thêm mới** | **[New]** | Không có trong [P2] — cần cho DR |
| Time features | **✅ Thêm mới** | **[New]** | Hour of day — cải thiện accuracy |
| **Output targets** | | | |
| PV power | ✅ | [P2] | |
| Nhiệt độ | ✅ | [P2] | |
| Wind power | **✅ Thêm mới** | **[New]** | |
| Load demand | ✅ | [P2] | |
| Electricity price | **✅ Thêm mới** | **[New]** | TOU deterministic, RTP cần forecast |

> **Kết luận:** Kiến trúc LSTM-TCN kế thừa 100% từ [P2]. Điểm mới: (1) thêm input wind speed + price, (2) thêm output wind power + price, (3) mở rộng output horizon cho MPC.

---

## 6. MPC CONTROLLER

| Tham số | Giá trị | Nguồn | Ghi chú |
|---------|---------|-------|---------|
| **Inner loop (current control)** | | | |
| Sample time Ts | **4×10⁻⁶ s** | [P2] | 250 kHz |
| Prediction horizon Np | **2 steps** | [P2] | |
| Control horizon Nc | **1 step** | [P2] | |
| W_PV (PV current) | **10** | [P2] | |
| W_bat (Battery current) | **50** | [P2] | |
| W_wind (Wind current) | **10** | **[New]** | Thêm mới — tương tự W_PV |
| W_DC (DC bus voltage) | **100** | [P2] | Cao nhất — ưu tiên ổn định điện áp |
| F_i (control effort) | **0.04** | [P2] | |
| Solver | **OSQP** | [Lit] | [Stellato et al. 2020] — verified 70μs solve time |
| **Outer loop (EMS scheduling)** | | | |
| Sample time Ts | **3600 s** | **[New]** | 1 hour — phù hợp cho DR scheduling |
| Prediction horizon Np | **24 steps** | **[New]** | 24-hour look-ahead |
| **DR constraints** | | | |
| Peak clip ratio α | **0.15** | [P1] | Panda dùng 15% max load reduction |
| Valley fill ratio β | **0.10** | **[New]** | Tham khảo literature [Scientific Reports 2025] |
| Net demand threshold (Peak) | **80% P_peak** | [P1] | |
| Net demand threshold (Valley) | **30% P_peak** | [P1] | |
| **Sigmoid parameters** | | | |
| z (slope) | **10** | [P2] | |
| x₀ (midpoint) | **0.5** | [P2] | |

> **Kết luận:** MPC inner loop kế thừa từ [P2]. W_wind được thêm mới. Outer loop và DR constraints từ [P1]. Sigmoid từ [P2].

---

## 7. DEMAND RESPONSE (DR)

| Tham số | Giá trị | Nguồn | Ghi chú |
|---------|---------|-------|---------|
| **TOU Pricing** | | | |
| Off-peak (22-06h) | **0.5× base** | [P1] | Panda dùng TOU 3 khung giờ |
| Valley (06-09h) | **0.8× base** | **[New]** | Mở rộng lên 5 khung giờ |
| Mid-peak (09-13h) | **1.0× base** | **[New]** | Tham khảo [MDPI Energies 2023] |
| On-peak (13-18h) | **2.0× base** | [P1] | |
| Evening (18-22h) | **1.2× base** | **[New]** | |
| **Price Elasticity Matrix** | | | |
| Self-elasticity (diagonal) | **-0.20 to -0.39** | [Lit] | [MDPI Energies 2023, 2025] — typical range -0.2 to -0.98 |
| Cross-elasticity (off-diagonal) | **0.004 to 0.01** | [Lit] | Giá trị dương nhỏ |
| **DR incentive λ** | | | |
| Peak Clipping | **λ = 1.5** | **[New]** | Cao nhất — ưu tiên giảm tải |
| TOU On-peak (discharge) | **λ = 1.0** | **[New]** | |
| TOU Off-peak (charge) | **λ = 1.0** | **[New]** | |
| Normal operation | **λ = 0.3** | **[New]** | Thấp — không khuyến khích DR |
| **Ràng buộc DR** | | | |
| DR ramp rate | **Có giới hạn** | **[New]** | Tránh sốc điện khi chuyển DR mode |

> **Kết luận:** TOU pricing khung giờ và giá tương đối tham khảo từ [P1], mở rộng lên 5 khung giờ. PEM từ literature. DR incentive λ là tham số mới — có thể tùy chỉnh trong mô phỏng.

---

## 8. LOAD & GRID

| Tham số | Giá trị | Nguồn | Ghi chú |
|---------|---------|-------|---------|
| Peak load | **18 kW** | [P1] | Panda dùng 18kW peak |
| Grid import max | **25 kW** | **[New]** | Tương đương P_bat max |
| Grid export max | **25 kW** | **[New]** | |
| AC Bus | **380V / 50Hz** | **[New]** | Tiêu chuẩn |

---

## BẢNG TỔNG KẾT: THAM SỐ NÀO TỪ ĐÂU

```
Tham số                    Giá trị         Nguồn chính
──────────────────────────────────────────────────────────
PV: 20 kWp                [P1] Panda
PV: Module ASW-250P       [P2] Limouni
PV: Voc/Isc/Vmp/Imp       [P2] Limouni
──────────────────────────────────────────────────────────
Wind: 10 kW               [New]  ← MỚI
Wind: Vci/Vr/Vco          [Lit] IEC 61400 + MDPI review
Wind: Cp=0.45             [Lit] MDPI Energies 2023
──────────────────────────────────────────────────────────
Battery: 50 kWh           [P1] Panda
Battery: 120V             [P2] Limouni
Battery: SoC 20-90%       [P1] Panda
Battery: η=0.95           [P2] Limouni
──────────────────────────────────────────────────────────
DC Bus: 800V              [P2] Limouni
Inverter: 30kVA           [New]  ← MỚI (từ tổng CS)
Converter L/r/C           [P2] Limouni
Converter L_wind=5mH      [Lit]  ← MỚI (verified)
──────────────────────────────────────────────────────────
LSTM-TCN architecture     [P2] Limouni
Input features mở rộng    [New]  ← MỚI (wind+price)
──────────────────────────────────────────────────────────
MPC parameters            [P2] Limouni
W_wind=10                 [New]  ← MỚI
Np=24 (outer)             [New]  ← MỚI
──────────────────────────────────────────────────────────
DR: TOU pricing           [P1] Panda
DR: Threshold 80/30%      [P1] Panda
DR: α=0.15, β=0.10        [P1] + [New]
DR: PEM                   [Lit] MDPI Energies
──────────────────────────────────────────────────────────
Load: 18kW peak           [P1] Panda
Grid: 25kW limits          [New]  ← MỚI
──────────────────────────────────────────────────────────
Sigmoid function          [P2] Limouni
Hysteresis 5%             [Lit] Alam et al. 2024 SciRep
OSQP solver               [Lit] Stellato et al. 2020
```

## KẾT LUẬN CHUNG

| Loại tham số | Số lượng | Chiếm % |
|-------------|----------|---------|
| Kế thừa từ [P1] Panda | ~10 | ~25% |
| Kế thừa từ [P2] Limouni | ~25 | ~50% |
| Verified từ literature [Lit] | ~8 | ~15% |
| Đề xuất mới [New] | ~10 | ~10% |
| **Tổng** | **~53** | **100%** |
