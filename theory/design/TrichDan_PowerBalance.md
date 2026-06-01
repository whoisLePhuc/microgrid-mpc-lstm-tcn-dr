# TRÍCH DẪN CHO CÔNG THỨC CÂN BẰNG CÔNG SUẤT

$$P_{PV} + P_{WT} + P_{bat} + P_{grid} = P_{load} - P_{DR}$$

---

## Cách trích dẫn cho tiểu luận

Công thức trên là sự kết hợp của 2 convention phổ biến trong literature. Bạn có thể trích dẫn từng phần như sau:

### Phần 1: Vế trái — Nguồn phát bằng tải

Các paper sau dùng convention **tổng phát = tổng tải** với các nguồn PV, Wind, Battery, Grid:

> **Paper A** — PMC 2024 (Nature):
> $$P_{PV} + P_{WIND} + P_{BATTERIES} + P_{GRID} = P_{LOAD}$$
>
> Trích dẫn: *"Oladosu, T. L., et al. (2024). A rule-based energy management system for hybrid renewable energy sources with battery bank optimized by genetic algorithm optimization. *Scientific Reports*, 14, 4953. https://doi.org/10.1038/s41598-024-55563-0"*

> **Paper B** — MDPI Energies 2018:
> $$P_{PV,t} + P_{WT,t} + P_{BES,t} + P_{grid,t} = P_{D,t}$$
>
> Trích dẫn: *"Ghaffari, A., & Askarzadeh, A. (2018). Grey Wolf Optimization-Based Optimum Energy-Management and Battery-Sizing Method for Grid-Connected Microgrids. *Energies*, 11(4), 847. https://doi.org/10.3390/en11040847"*

> **Paper C** — MDPI Sustainability 2022:
> $$(P_{PV} + P_{WT} \pm P_{ESU}) + P_{Gen} \pm P_{Grid} = P_{Load}$$
>
> Trích dẫn: *"Mohammed, A., et al. (2022). The Potential Role of Hybrid Renewable Energy System for Grid Intermittency Problem: A Techno-Economic Optimisation and Comparative Analysis. *Sustainability*, 14(21), 14045."*

### Phần 2: Vế phải — DR làm giảm tải

Các paper sau cho thấy DR (load reduction) nằm **bên phải** phương trình với dấu trừ:

> **Paper D** — arXiv 2025 (MILP-DR Framework):
> $$P_{grid} + P_{solar} + (P_{dis} - P_{ch}) = P_{load} - P_{red} + \dots$$
>
> Trích dẫn: *"Demand Response Optimization MILP Framework for Microgrids with DERs. (2025). *arXiv:2502.08764*. Equation (23)."*

> **Paper E** — MDPI Energies 2023 (DRP for microgrid):
> $$P_w + P_{pv} + P_{bd} - P_{bc} = P_L^{DRP}$$
>
> Trong đó $P_L^{DRP}$ là tải sau khi áp dụng DR — **tương đương** $P_{load} - P_{DR}$
>
> Trích dẫn: *"Olatomiwa, L., et al. (2023). Optimal Capacity and Operational Planning for Renewable Energy-Based Microgrid Considering Different Demand-Side Management Strategies. *Energies*, 16(10), 4147."*

> **Paper F** — MDPI Energies 2021 (Islanded Microgrid với DRP):
> $$P_{pv} + P_w + P_{discharge} = D_{DR} + P_{charge}$$
>
> Trong đó $D_{DR}$ là "Demand after DR" — tương đương $P_{load} - P_{DR}$
>
> Trích dẫn: *"Evaluating the Effect of Demand Response Programs (DRPs) on Robust Optimal Sizing of Islanded Microgrids. (2021). *Energies*, 14(18), 5750. Equation (16)."*

---

## Cách viết trong tiểu luận (đề xuất)

Trong phần **Chương 3 — Xây dựng mô hình hệ thống**, bạn viết:

> Cân bằng công suất tại bus AC được biểu diễn bởi phương trình:
>
> $$P_{PV}(t) + P_{WT}(t) + P_{bat}(t) + P_{grid}(t) = P_{load}(t) - P_{DR}(t) \tag{3.7}$$
>
> Trong đó $P_{DR}(t) > 0$ tương ứng với Peak Clipping (cắt giảm tải) và $P_{DR}(t) < 0$ tương ứng với Valley Filling (tăng tải). Công thức này nhất quán với các nghiên cứu trước đây: vế trái gồm các nguồn phát (PV, wind, battery, lưới) [Oladosu 2024; Ghaffari 2018], và vế phải là tải sau khi trừ đi lượng DR [arXiv 2502.08764 2025; Olatomiwa 2023].

> **Giải thích ngắn:** Cách trình bày này thể hiện bản chất vật lý: DR tác động vào phía tải, làm thay đổi lượng công suất thực tế cần cung cấp từ các nguồn phát. Khi DR cắt tải ($P_{DR}>0$), nhu cầu phát giảm. Khi DR tăng tải ($P_{DR}<0$), nhu cầu phát tăng.

---

## Tài liệu tham khảo đầy đủ (để đưa vào danh mục)

**[Oladosu 2024]** Oladosu, T. L., et al. (2024). A rule-based energy management system for hybrid renewable energy sources with battery bank optimized by genetic algorithm optimization. *Scientific Reports*, 14, 4953. https://doi.org/10.1038/s41598-024-55563-0

**[Ghaffari 2018]** Ghaffari, A., & Askarzadeh, A. (2018). Grey Wolf Optimization-Based Optimum Energy-Management and Battery-Sizing Method for Grid-Connected Microgrids. *Energies*, 11(4), 847. https://doi.org/10.3390/en11040847

**[arXiv 2502.08764]** Demand Response Optimization MILP Framework for Microgrids with DERs. (2025). *arXiv:2502.08764*.

**[Olatomiwa 2023]** Olatomiwa, L., et al. (2023). Optimal Capacity and Operational Planning for Renewable Energy-Based Microgrid Considering Different Demand-Side Management Strategies. *Energies*, 16(10), 4147.

**[Mohammed 2022]** Mohammed, A., et al. (2022). The Potential Role of Hybrid Renewable Energy System for Grid Intermittency Problem. *Sustainability*, 14(21), 14045.
