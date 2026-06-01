# HỆ THỐNG NGHIÊN CỨU — PV-WIND-BATTERY MICROGRID VỚI DEMAND RESPONSE

---

## 1. HỆ THỐNG VẬT LÝ GỒM NHỮNG GÌ?

```mermaid
graph TB
    subgraph LEGEND["CHÚ THÍCH"]
        PWR("────► Dòng điện (Power)")
        SIG("- - ► Tín hiệu điều khiển")
    end

    subgraph AC_SIDE["Phía AC - Lưới điện"]
        BUS["AC Bus<br/>380V / 50Hz"]
        LOAD["📊 Tải tiêu thụ<br/>Peak 18kW"]
        GRID["🔌 Lưới điện quốc gia"]
    end

    subgraph DC_SIDE["Phía DC - Nguồn phát"]
        PV["☀️ Solar PV Array<br/>20 kWp<br/>80 module ASW-250P"]
        WT["💨 Wind Turbine<br/>10 kW<br/>Vcut-in=3, Vrated=12, Vcut-out=25<br/>Rotor D=7m"]
        BESS["🔋 Battery Storage<br/>50 kWh, 120V<br/>SoC: 20% - 90%"]
    end

    subgraph CONVERSION["Bộ biến đổi"]
        INV["⚡ Bidirectional Inverter<br/>30 kVA<br/>DC ↔ AC"]
        B_PV["DC/DC Boost<br/>PV → DC Bus"]
        B_WT["DC/DC Boost<br/>Wind → DC Bus"]
        B_BAT["DC/DC Bidirectional<br/>Battery ↔ DC Bus"]
    end

    subgraph DC_BUS["DC Bus 800V"]
        DCBUS["── DC Bus ──"]
    end

    PV --> B_PV
    B_PV --> DCBUS
    WT --> B_WT
    B_WT --> DCBUS
    BESS <--> B_BAT
    B_BAT <--> DCBUS
    DCBUS --> INV
    INV <--> BUS
    BUS --- LOAD
    BUS --- GRID
```

**Giải thích bằng lời:**

| Thiết bị | Thông số | Làm gì? |
|----------|---------|---------|
| ☀️ **PV Array** | 20 kWp, 80 tấm pin ASW-250P | Biến ánh sáng mặt trời thành điện DC |
| 💨 **Wind Turbine** | 10 kW, rotor 7m | Biến gió thành điện AC, chỉnh lưu thành DC |
| 🔋 **Battery** | 50 kWh, Lithium-Ion 120V | Tích trữ điện dư, xả khi thiếu |
| ⚡ **Inverter** | 30 kVA | Chuyển DC↔AC, kết nối với lưới |
| 🔌 **Grid** | Lưới quốc gia | Mua/bán điện khi cần |

---

## 2. HỆ THỐNG ĐIỀU KHIỂN CÓ NHỮNG THÀNH PHẦN NÀO?

```mermaid
graph TB
    subgraph SENSORS["LỚP ĐO LƯỜNG (Sensors)"]
        S_V["Cảm biến: Vpv, Ipv"]
        S_W["Cảm biến: Vwind, Iwind"]
        S_B["Cảm biến: Vbat, Ibat, SOC"]
        S_G["Cảm biến: Vgrid, Igrid"]
        S_L["Cảm biến: Pload"]
    end

    subgraph FORECAST["LỚP DỰ BÁO (LSTM-TCN)"]
        F1["Dự báo GHI + Nhiệt độ<br/>→ Công suất PV"]
        F2["Dự báo Tốc độ gió<br/>→ Công suất Wind"]
        F3["Dự báo Nhu cầu tải"]
        F4["Dự báo Giá điện (TOU)"]
    end

    subgraph DECISION["LỚP RA QUYẾT ĐỊNH"]
        PMS["Power Management System<br/>Chọn 1 trong 6 mode<br/>(M1-M6)"]
        DR_LOGIC["DR Logic<br/>Peak Clipping / Valley Fill / TOU"]
        MPC["Model Predictive Control<br/>Giải bài toán tối ưu mỗi bước"]
    end

    subgraph ACTUATORS["LỚP CHẤP HÀNH"]
        A_PV["Điều khiển<br/>PV Boost Converter"]
        A_WT["Điều khiển<br/>Wind Boost Converter"]
        A_BAT["Điều khiển<br/>Battery Converter"]
        A_INV["Điều khiển<br/>Inverter → Grid"]
    end

    S_V --> F1
    S_W --> F2
    S_L --> F3
    S_G --> F4

    F1 --> PMS
    F2 --> PMS
    F3 --> PMS
    F4 --> DR_LOGIC
    S_B --> PMS
    S_B --> DR_LOGIC

    PMS --> MPC
    DR_LOGIC --> MPC

    MPC --> A_PV
    MPC --> A_WT
    MPC --> A_BAT
    MPC --> A_INV
```

---

## 3. DÒNG NĂNG LƯỢNG ĐI NHƯ THẾ NÀO?

### 3.1 Khi nắng to, gió mạnh (Thừa năng lượng)

```mermaid
flowchart LR
    PV["☀️ PV 20kW"] --> BUSDC["DC Bus<br/>800V"]
    WT["💨 Wind 10kW"] --> BUSDC
    
    BUSDC --> INV["Inverter"]
    INV --> LOAD["⚡ Tải 12kW"]
    INV --> GRID["🔌 Bán lên lưới<br/>18kW"]
    INV --> BATT["🔋 Sạc pin<br/>từ surplus"]
```

**Tổng phát = 30kW, Tải = 12kW → Dư 18kW → Sạc pin + Bán lưới**

### 3.2 Khi tối, lặng gió (Thiếu năng lượng)

```mermaid
flowchart LR
    PV["☀️ PV 0kW"] --> BUSDC
    WT["💨 Wind 2kW"] --> BUSDC
    BATT["🔋 Xả pin<br/>8kW"] --> BUSDC
    GRID["🔌 Mua từ lưới<br/>5kW"] --> INV
    INV --> BUSDC
    BUSDC --> LOAD["⚡ Tải 15kW"]
```

**Tổng phát = 2kW, Tải = 15kW → Thiếu 13kW → Xả pin + Mua lưới**

### 3.3 DR kích hoạt (Cắt tải đỉnh)

```mermaid
flowchart LR
    PV["☀️ PV 3kW"] --> BUSDC
    WT["💨 Wind 5kW"] --> BUSDC
    BATT["🔋 Xả pin<br/>10kW"] --> BUSDC
    GRID["🔌 Mua từ lưới<br/>2kW"] --> INV
    INV --> BUSDC
    
    BUSDC --> LOAD["⚡ Tải 20kW"]
    DR["🎯 DR Peak Clip<br/>Cắt 15% tải<br/>= 3kW"] -.->|Giảm tải| LOAD
    
    NOTE["Tải còn 17kW<br/>vừa đủ từ PV+Wind+Battery+Grid"] --> LOAD
```

---

## 4. BAO NHIÊU LỚP ĐIỀU KHIỂN?

```mermaid
graph TB
    subgraph L1["LỚP 1: EMS (Energy Management System)"]
        E01["Lập lịch 24 giờ"]
        E02["TOU Pricing + DR Schedule"]
        E03["Mục tiêu: Tối ưu chi phí"]
        note1["⏱ Chạy mỗi 1 giờ"]
    end

    subgraph L2["LỚP 2: MPC (Model Predictive Control)"]
        M01["Dự báo (LSTM-TCN)"]
        M02["Giải QP tối ưu"]
        M03["Xuất duty cycle cho converter"]
        note2["⏱ Chạy mỗi 250 kHz (4μs)"]
    end

    subgraph L3["LỚP 3: Power Converters"]
        C01["PV Boost"]
        C02["Wind Boost"]
        C03["Battery Bidirectional"]
        C04["Grid Inverter"]
        note3["⏱ Chạy liên tục"]
    end

    L1 --> L2 --> L3
```

---

## 5. PMS CÓ 6 CHẾ ĐỘ HOẠT ĐỘNG NÀO?

```mermaid
stateDiagram-v2
    [*] --> CHECK: Đo Ppv, Pwind, Pload
    
    state CHECK <<choice>>
    
    CHECK --> EPM: Tổng phát ≥ Tải (thừa)
    CHECK --> DPM: Tổng phát < Tải (thiếu)
    
    state EPM {
        [*] --> SOC_HIGH: SoC < 85%?
        SOC_HIGH --> M1_Charge: ✅ Dưới 85% → Sạc pin
        SOC_HIGH --> DR_CHECK: ❌ Đã đầy (≥85%)
        
        DR_CHECK --> M2_ValleyFill: Giờ thấp điểm? → Sạc thêm từ lưới (giá rẻ)
        DR_CHECK --> M3_Export: Không → Bán hết lên lưới
    }
    
    state DPM {
        [*] --> SOC_LOW: SoC > 30%?
        SOC_LOW --> DR_CHECK2: ✅ Còn pin
        SOC_LOW --> M6_GridImport: ❌ Cạn pin → Mua từ lưới
        
        DR_CHECK2 --> M4_PeakClip: Giờ cao điểm? → Xả pin + cắt tải
        DR_CHECK2 --> M5_Discharge: Không → Xả pin bình thường
    }
```

**6 chế độ tóm tắt:**

```
THỪA NĂNG LƯỢNG (Pgen > Pload):
  M1: Pin chưa đầy (<85%)   → SẠC PIN
  M2: Pin đã đầy + giá rẻ    → VALLEY FILL (sạc từ lưới để hưởng giá rẻ)
  M3: Pin đã đầy + giá thường → BÁN LƯỚI

THIẾU NĂNG LƯỢNG (Pgen < Pload):
  M4: Pin còn + giá đắt      → PEAK CLIP (xả pin + cắt tải 15%)
  M5: Pin còn + giá thường   → XẢ PIN bình thường
  M6: Pin hết                → MUA LƯỚI
```

---

## 6. DEMAND RESPONSE HOẠT ĐỘNG THẾ NÀO?

```mermaid
flowchart TD
    START["Mỗi bước thời gian k"] --> PRICE_CHECK{"Giờ nào?"}
    
    PRICE_CHECK -->|"13:00-18:00<br/>Cao điểm"| PEAK["🏷️ Giá ĐẮT<br/>→ BESS nên xả"]
    PRICE_CHECK -->|"22:00-06:00<br/>Thấp điểm"| OFFPEAK["🏷️ Giá RẺ<br/>→ BESS nên sạc"]
    PRICE_CHECK -->|"Giờ khác<br/>Bình thường"| MID["🏷️ Giá TB<br/>→ BESS tự do"]
    
    PEAK --> NET_CHECK{"P_net > 80%<br/>peak demand?"}
    OFFPEAK --> NET_CHECK2{"P_net < 30%<br/>peak demand?"}
    MID --> NORMAL["Không DR"]
    
    NET_CHECK -->|Yes| CLIP["🚨 PEAK CLIP!<br/>Xả BESS + cắt 15% tải<br/>→ λ = 1.5 (incentive cao)"]
    NET_CHECK -->|No| NORMAL
    
    NET_CHECK2 -->|Yes| FILL["🚨 VALLEY FILL!<br/>Sạc BESS từ lưới<br/>→ tăng tải 10%"]
    NET_CHECK2 -->|No| NORMAL
    
    CLIP --> MPC["MPC giải bài toán<br/>có DR term"]
    FILL --> MPC
    NORMAL --> MPC
```

**Cơ chế DR là 2 lớp (2-layer DR):**

```
LỚP 1 - Price-based:
  • Giá cao điểm (13-18h)  → Khuyến khích xả pin
  • Giá thấp điểm (22-6h)  → Khuyến khích sạc pin
  • Đây là DR GIÁN TIẾP (BESS tự arbitrage)

LỚP 2 - Threshold-based (bổ sung):
  • Nếu net > 80% peak → Peak Clipping (cắt tải)
  • Nếu net < 30% peak → Valley Filling (tăng tải)
  • Đây là DR TRỰC TIẾP (có incentive λ)
```

---

## 7. MPC GIẢI BÀI TOÁN GÌ MỖI BƯỚC?

```mermaid
flowchart TD
    START["Bắt đầu bước k"] --> MEAS["ĐO: Vpv, Ipv, Ibat, Iwind, VDC, SOC"]
    
    MEAS --> FORECAST["DỰ BÁO: LSTM-TCN cho ra<br/>ĜHI, T̂emp, Ŵspd, L̂oad, P̂rice<br/>(H bước tiếp theo)"]
    
    FORECAST --> PMS_MODE["PMS: Chọn mode (M1-M6)"]
    FORECAST --> DR_MODE["DR: Tính λ, P_DR_max"]
    
    PMS_MODE --> REF["TÍNH: Dòng tham chiếu<br/>I_PV_ref, I_bat_ref, I_wind_ref"]
    DR_MODE --> REF
    
    REF --> SIG["LÀM MƯỢT: Sigmoid function"]
    
    SIG --> QP["GIẢI QP:"]
    
    QP --> OBJ["Minimize J = W_pv·ΔI_pv² + W_bat·ΔI_bat² + W_wind·ΔI_wind²<br/>+ W_DC·ΔV_DC²<br/>+ C_grid·P_grid (giá điện)<br/>- λ_DR·P_DR (DR incentive)"]
    
    QP --> CONS["Subject to:<br/>• SOC 20-90%<br/>• I ≤ I_max<br/>• V_DC 720-880V<br/>• 0 ≤ P_DR ≤ 0.15·P_load"]
    
    QP --> SOLVE["OSQP Solver (~70μs)"]
    
    SOLVE --> CHECK{"Feasible?"}
    CHECK -->|Yes| APPLY["ÁP DỤNG: U_PV, U_bat, U_wind"]
    CHECK -->|No| SOFT["NỚI LỎNG: Slack variable"]
    SOFT --> QP
    
    APPLY --> SHIFT["DỊCH: k = k+1"]
    SHIFT --> MEAS
```

---

## 8. DỮ LIỆU CHẠY QUA CÁC MODULE THẾ NÀO?

```mermaid
sequenceDiagram
    participant MT as Môi trường
    participant PV as PV Panel
    participant WT as Wind Turbine
    participant BAT as Battery
    participant LSTM as LSTM-TCN
    participant PMS as PMS
    participant DR as DR Logic
    participant MPC as MPC Controller
    participant GRID as Lưới điện

    loop Mỗi giây (inner loop: 4μs)
        PV->>LSTM: GHI, Nhiệt độ
        WT->>LSTM: Tốc độ gió
        GRID->>LSTM: Giá điện (TOU)
        
        LSTM->>LSTM: Dự báo H bước
        LSTM->>PMS: Công suất dự báo
        LSTM->>DR: Giá + Tải dự báo
        
        PMS->>PMS: Chọn mode M1-M6
        DR->>DR: Tính λ_DR, P_DR_max
        
        PMS->>MPC: I_ref theo mode
        DR->>MPC: λ_DR, P_DR_max
        
        PV->>MPC: Vpv, Ipv hiện tại
        WT->>MPC: Vwind, Iwind hiện tại
        BAT->>MPC: Vbat, Ibat, SOC
        
        MPC->>MPC: Giải QP
        MPC->>PV: Duty cycle U_PV
        MPC->>WT: Duty cycle U_wind
        MPC->>BAT: Duty cycle U_bat
        MPC->>GRID: P_grid tham chiếu
    end
```

---

## 9. TỔNG KẾT: MÔ HÌNH NGHIÊN CỨU LÀ GÌ?

```
┌────────────────────────────────────────────────────────────────────┐
│                 MÔ HÌNH NGHIÊN CỨU (RESEARCH MODEL)                │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  "XÂY DỰNG HỆ THỐNG ĐIỀU KHIỂN THỜI GIAN THỰC CHO MICROGRID      │
│   NỐI LƯỚI GỒM PIN MẶT TRỜI, TUABIN GIÓ, PIN LITHIUM-ION,         │
│   TÍCH HỢP DEMAND RESPONSE SỬ DỤNG MPC VÀ LSTM-TCN"               │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  HỆ THỐNG VẬT LÝ:    PV 20kW + Wind 10kW + Battery 50kWh         │
│                       + Inverter 30kVA + Grid                      │
│                                                                    │
│  BỘ ĐIỀU KHIỂN:      MPC (Model Predictive Control)               │
│                       - Inner loop: 250kHz (dòng điện)             │
│                       - Outer loop: 1h (EMS scheduling)            │
│                                                                    │
│  BỘ DỰ BÁO:          LSTM-TCN (2 LSTM layers + 3 TCN blocks)      │
│                       - Đầu vào: GHI, Temp, Wind, Load, Price      │
│                       - Đầu ra: PV, Wind, Load, Price (H bước)     │
│                                                                    │
│  DEMAND RESPONSE:     2 lớp:                                       │
│                       - Lớp 1: Price-based (TOU 5 khung giờ)       │
│                       - Lớp 2: Threshold-based (Peak/Valley)       │
│                                                                    │
│  PMS:                 6 modes (M1-M6)                              │
│                       - EPM: Charge / ValleyFill / Export          │
│                       - DPM: PeakClip / Discharge / Import         │
│                                                                    │
│  MỤC TIÊU:           Ổn định điện áp DC bus (VRI < 3%)            │
│                       Tiết kiệm chi phí (15-20%)                   │
│                       Tận dụng NLTT (> 90%)                        │
│                       Giảm peak demand (15-20%)                    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## PHỤ LỤC: CÁC CÔNG THỨC CHÍNH

### PV
$$P_{PV} = \eta_{PV} \times A \times G$$

### Wind
$$P_{WT}(t) = \begin{cases} 
0 & V < V_{ci} \\ 
\frac{1}{2} \rho A V^3 C_p & V_{ci} \leq V < V_r \\
P_{rated} & V_r \leq V \leq V_{co} \\
0 & V > V_{co}
\end{cases}$$

### Battery
$$SoC(k+1) = SoC(k) + \frac{\eta_{ch} P_{ch} \Delta t}{E_{bat}} - \frac{P_{dch} \Delta t}{\eta_{dch} E_{bat}}$$

### Power Balance
$$P_{PV} + P_{WT} + P_{bat} + P_{grid} = P_{load} - P_{DR}$$

### MPC Cost Function
$$J(k) = W_{PV} \Delta I_{PV}^2 + W_{bat} \Delta I_{bat}^2 + W_{wind} \Delta I_{wind}^2 + W_{DC} \Delta V_{DC}^2 + C_{grid} P_{grid} - \lambda_{DR} P_{DR}$$

### DR Threshold Logic
$$\text{Peak Clip: } 0 \leq P_{DR} \leq 0.15 P_{load} \quad \text{khi } P_{net} > 0.8 P_{peak}$$
$$\text{Valley Fill: } -0.10 P_{load} \leq P_{DR} \leq 0 \quad \text{khi } P_{net} < 0.3 P_{peak}$$
