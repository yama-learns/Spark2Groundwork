#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自測用的假感測器：**一定會崩潰**。

⛔ 它存在的唯一理由，是證明 `run_all_sensors.py` 把「崩潰」判成 INCOMPLETE 而不是 FAIL。
⚠️ 實測個案：兩支真感測器在 cp950 環境下 `UnicodeEncodeError` 當掉 → exit 1 →
   總結印「整套 FAIL」，**而真正發生的是它們沒跑完**（`R-22`、憲章 §7.4）。
"""
raise RuntimeError("deliberate crash for the self-test")
