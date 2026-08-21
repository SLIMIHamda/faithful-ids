# Extractor audit — annotation chunk 02 of 03

You are annotating explanation texts about network-traffic classification. Read
each text and report **what the text itself claims**. No other context is needed
and none is relevant.

## Task

For each item, list **every feature the text makes a directional claim about**,
and the direction the text asserts:

- `"+"` — the text says the feature raises / pushes up the score for the class it argues for
- `"-"` — the text says it lowers / pushes down that score
- `"unclear"` — the text names the feature but gives no explicit directional evidence

Set `"hedged": true` when a direction is softened ("may slightly reduce").

## What counts as a directional claim

**Only mark `+` or `-` when the text gives explicit evidence of the direction.**
The text must say something about the feature's *effect*: that it increases,
raises, lowers, reduces, drives, contributes to, adds to, weakens, or otherwise
moves the score — or give a signed value for it.

**Describing the feature's value is not a directional claim.** "A high PSH Flag
Count (1.0) suggests potential payload manipulation typical of botnet activity"
says the value is high and reads it as suspicious; it does not say the feature
raises the score. That is **`unclear`**. So is "unusually large", "within normal
bounds", "consistent with automated traffic" — unless the sentence also states
the effect on the score.

When you find yourself inferring the direction from what the feature *means*
rather than reading it in the text, the answer is `unclear`.

## Rules

1. Report **only what the prose says**, not whether it is correct about the
   traffic, and not what you can infer about it.
2. Use the **canonical feature name** from the vocabulary below, even when the
   text paraphrases it ("maximum forward packet length" -> `Fwd Packet Length Max`).
3. A feature the text does not mention is simply left out. Do not emit `absent` rows.
4. If a text mentions no feature at all, emit `"claims": []`.
5. Output one JSON object per line (JSONL), one line per item, in the order
   given, inside a single fenced code block. No commentary.

## Output format

```jsonl
{"item_id": "aud2-000", "claims": [{"feature": "Flow Duration", "dir": "+", "hedged": false}]}
```

## Feature vocabulary (use these exact names)

- `ACK Flag Count`
- `Active Max`
- `Active Mean`
- `Active Min`
- `Active Std`
- `Average Packet Size`
- `Avg Bwd Segment Size`
- `Avg Fwd Segment Size`
- `Bwd Avg Bulk Rate`
- `Bwd Avg Bytes/Bulk`
- `Bwd Avg Packets/Bulk`
- `Bwd Header Length`
- `Bwd IAT Max`
- `Bwd IAT Mean`
- `Bwd IAT Min`
- `Bwd IAT Std`
- `Bwd IAT Total`
- `Bwd PSH Flags`
- `Bwd Packet Length Max`
- `Bwd Packet Length Mean`
- `Bwd Packet Length Min`
- `Bwd Packet Length Std`
- `Bwd Packets/s`
- `Bwd URG Flags`
- `CWE Flag Count`
- `Down/Up Ratio`
- `ECE Flag Count`
- `FIN Flag Count`
- `Flow Bytes/s`
- `Flow Duration`
- `Flow IAT Max`
- `Flow IAT Mean`
- `Flow IAT Min`
- `Flow IAT Std`
- `Flow Packets/s`
- `Fwd Avg Bulk Rate`
- `Fwd Avg Bytes/Bulk`
- `Fwd Avg Packets/Bulk`
- `Fwd Header Length`
- `Fwd IAT Max`
- `Fwd IAT Mean`
- `Fwd IAT Min`
- `Fwd IAT Std`
- `Fwd IAT Total`
- `Fwd PSH Flags`
- `Fwd Packet Length Max`
- `Fwd Packet Length Mean`
- `Fwd Packet Length Min`
- `Fwd Packet Length Std`
- `Fwd Packets/s`
- `Fwd URG Flags`
- `Idle Max`
- `Idle Mean`
- `Idle Min`
- `Idle Std`
- `Init_Win_bytes_backward`
- `Init_Win_bytes_forward`
- `Max Packet Length`
- `Min Packet Length`
- `PSH Flag Count`
- `Packet Length Mean`
- `Packet Length Std`
- `Packet Length Variance`
- `RST Flag Count`
- `SYN Flag Count`
- `Subflow Bwd Bytes`
- `Subflow Bwd Packets`
- `Subflow Fwd Bytes`
- `Subflow Fwd Packets`
- `Total Backward Packets`
- `Total Fwd Packets`
- `Total Length of Bwd Packets`
- `Total Length of Fwd Packets`
- `URG Flag Count`
- `act_data_pkt_fwd`
- `min_seg_size_forward`

---

## Items


### aud2-025

```
Explanation:  
1. High Init_Win_bytes_backward significantly increased the Bot score by 3.1951.  
2. Bwd IAT Min further increased the Bot score by 3.0518.  
3. Flow IAT Max contributed to the Bot score with an increase of 2.5033.  
4. Fwd IAT Max added to the Bot score with an increase of 1.6841.  
5. Bwd Packet Length Max also raised the Bot score by 1.6075.  

The decision to classify the instance as Bot was driven by multiple factors that collectively increased the Bot score.
```

### aud2-026

```
SHAP attribution (top-5) for class DDoS: act_data_pkt_fwd=+1.5998; Init_Win_bytes_backward=+1.3344; Fwd Packet Length Max=+1.2650; Total Length of Fwd Packets=+1.2297; Init_Win_bytes_forward=-0.6668
```

### aud2-027

```
SHAP attribution (top-5) for class PortScan: Total Length of Fwd Packets=+2.1036; Bwd Packets/s=+1.2072; Init_Win_bytes_forward=+1.1976; PSH Flag Count=+1.0046; Flow Duration=+0.7669
```

### aud2-028

```
The flow was classified as **FTP-Patator** due to several key features indicating automated brute-force attempts. A **SYN Flag Count = 1.0** suggests initiation of a connection, while **Fwd PSH Flags = 1.0** and **Fwd Packet Length Mean = 7.0** indicate data transmission behavior typical of FTP. Additionally, **Flow Duration = 230.0** and **Flow Packets/s = 13043.47826** suggest high-frequency, short-lived connections, consistent with automated login attempts. These features align with the pattern of FTP-Patator, which systematically tries credentials.
```

### aud2-029

```
The flow was classified as **Web Attack** due to the presence of **PSH Flag Count = 1.0**, which suggests potential payload manipulation, and **Subflow Fwd Packets = 3.0**, indicating fragmented or unusual packet behavior. Additionally, **Bwd Header Length = 40.0** and **Fwd Header Length = 104.0** suggest abnormal header sizes, which may indicate attempts to bypass security filters. These features collectively point toward suspicious network behavior consistent with a Web Attack.
```

### aud2-030

```
This flow was classified as **DDoS** due to high **Flow Packets/s** (89.78) and **Bwd Packets/s** (51.31), indicating a high rate of packets, which is common in DDoS attacks. The **Flow Duration** (77,965 ms) and **Bwd IAT Std** (44,110.52) suggest irregular intervals between packets, a sign of distributed traffic. Additionally, the **Bwd Header Length** (92.0) and **Bwd Packet Length Std** (5,795.50) show large and variable packet sizes, which can indicate malicious traffic patterns.
```

### aud2-031

```
The flow was classified as **PortScan** due to high **Bwd Packets/s** (15,151.52) and **Flow Packets/s** (30,303.03), indicating a high rate of packets sent in a short time, typical of scanning behavior. The **PSH Flag Count** is 1.0, suggesting attempts to push data, often seen in scans. Additionally, **Flow Duration** (66.0) and **Flow IAT Std** (0.0) show a very short and consistent interval between packets, further supporting the scan pattern.
```

### aud2-032

```
SHAP attribution (top-5) for class Bot: Init_Win_bytes_backward=+4.5495; Bwd IAT Std=+1.4471; Init_Win_bytes_forward=+1.2292; Bwd Packet Length Max=+0.9696; Total Length of Bwd Packets=+0.8811
```

### aud2-033

```
Explanation:  
The highest contributing factor was Max Packet Length, which increased the FTP-Patator score by 6.3059. Next, Bwd Header Length also increased the score by 5.8738. Fwd Packet Length Std contributed by increasing the score by 3.3756. Packet Length Std further increased the score by 1.1028. Finally, Init_Win_bytes_backward added 0.7394 to the FTP-Patator score.  

Overall decision: The network traffic was classified as FTP-Patator due to the cumulative effect of these contributing factors increasing the predicted score.
```

### aud2-034

```
SHAP attribution (top-5) for class DoS: Init_Win_bytes_backward=+2.9496; Idle Min=+0.9958; Idle Mean=+0.9613; Bwd Packet Length Std=+0.7817; FIN Flag Count=+0.6414
```

### aud2-035

```
The model classified this flow as Web Attack. The most influential factors were: 1. Fwd IAT Min increased the Web Attack score (magnitude 7.4495); 2. Max Packet Length increased the Web Attack score (magnitude 4.7825); 3. Flow IAT Min increased the Web Attack score (magnitude 2.0858); 4. Init_Win_bytes_backward increased the Web Attack score (magnitude 1.2049); 5. Flow Duration increased the Web Attack score (magnitude 0.9704).
```

### aud2-036

```
SHAP attribution (top-5) for class FTP-Patator: Max Packet Length=+6.3059; Bwd Header Length=+5.8738; Packet Length Std=+0.9814; Average Packet Size=+0.7531; Flow Duration=-0.7240
```

### aud2-037

```
The model classified this flow as Bot. The most influential factors were: 1. Init_Win_bytes_backward increased the Bot score (magnitude 5.0289); 2. Init_Win_bytes_forward increased the Bot score (magnitude 3.5115); 3. Fwd Header Length increased the Bot score (magnitude 1.9376); 4. Flow Bytes/s increased the Bot score (magnitude 1.0307); 5. Fwd Packets/s increased the Bot score (magnitude 0.5474).
```

### aud2-038

```
The model classified this flow as DoS. The most influential factors were: 1. Init_Win_bytes_forward increased the DoS score (magnitude 2.7883); 2. Average Packet Size increased the DoS score (magnitude 1.1829); 3. Bwd Packets/s increased the DoS score (magnitude 1.1344); 4. Fwd Packets/s increased the DoS score (magnitude 1.1151); 5. Flow IAT Max increased the DoS score (magnitude 0.5386).
```

### aud2-039

```
SHAP attribution (top-5) for class FTP-Patator: Max Packet Length=+6.3059; Bwd Header Length=+5.8738; Fwd Packet Length Std=+3.4468; Packet Length Std=+1.0859; Init_Win_bytes_backward=+0.7394
```

### aud2-040

```
Explanation:  
The act_data_pkt_fwd value significantly increased the DDoS score by 2.7415, indicating a strong association with DDoS activity. The Init_Win_bytes_forward further increased the score by 1.4088, suggesting forward data transmission patterns typical of DDoS attacks. Total Backward Packets added 1.1466 to the score, highlighting unusual backward traffic behavior. Fwd Packet Length Max contributed 0.6766, pointing to large packet sizes often seen in DDoS attacks. Flow IAT Min added 0.6231, showing minimal intervals between packets, a common characteristic in DDoS scenarios.  

Overall decision: The system classified the network flow as a DDoS attack
```

### aud2-041

```
The model classified this flow as DoS. The most influential factors were: 1. Init_Win_bytes_backward increased the DoS score (magnitude 3.0045); 2. Idle Min increased the DoS score (magnitude 0.9849); 3. Idle Mean increased the DoS score (magnitude 0.9684); 4. Bwd Packet Length Std increased the DoS score (magnitude 0.7922); 5. FIN Flag Count increased the DoS score (magnitude 0.6434).
```

### aud2-042

```
The model classified this flow as Web Attack. The most influential factors were: 1. Init_Win_bytes_forward increased the Web Attack score (magnitude 4.5109); 2. Init_Win_bytes_backward increased the Web Attack score (magnitude 4.0522); 3. URG Flag Count increased the Web Attack score (magnitude 0.9659); 4. min_seg_size_forward increased the Web Attack score (magnitude 0.6676); 5. Flow Duration increased the Web Attack score (magnitude 0.5196).
```

### aud2-043

```
Explanation:  
1. High Init_Win_bytes_backward significantly increased the Bot score by 5.0289.  
2. High Init_Win_bytes_forward further increased the Bot score by 3.5115.  
3. Increased Fwd Header Length added 1.9376 to the Bot score.  
4. Elevated Flow Bytes/s contributed 1.0307 to the Bot score.  
5. Higher Fwd Packets/s added 0.5474 to the Bot score.  

The model predicted **Bot** based on the cumulative impact of these contributing factors.
```

### aud2-044

```
SHAP attribution (top-5) for class Web Attack: Fwd IAT Min=+7.3025; Max Packet Length=+4.7825; Flow IAT Min=+1.9237; Init_Win_bytes_backward=+0.8456; min_seg_size_forward=+0.8427
```

### aud2-045

```
Explanation:  
1. A high value in Init_Win_bytes_forward significantly increased the SSH-Patator score by 5.0303.  
2. A high value in Init_Win_bytes_backward further increased the SSH-Patator score by 4.4092.  
3. A high count of URG Flags increased the SSH-Patator score by 3.8950.  
4. A larger min_seg_size_forward increased the SSH-Patator score by 1.0347.  
5. A higher Bwd Packets/s increased the SSH-Patator score by 0.8035.  

Overall decision: The network activity strongly indicates an SSH-Patator attack based on the cumulative contribution of these features
```

### aud2-046

```
SHAP attribution (top-5) for class FTP-Patator: Total Length of Fwd Packets=+4.1582; Fwd PSH Flags=+4.0821; Fwd Packet Length Std=+2.5015; Init_Win_bytes_forward=+1.3521; Packet Length Std=+1.2594
```

### aud2-047

```
Explanation:  
The highest contributing factor was Max Packet Length, which increased the FTP-Patator score by 6.3059. Next, Bwd Header Length also increased the score by 5.8738. Fwd Packet Length Std contributed by increasing the score by 3.4468. Packet Length Std further increased the score by 1.0859. Finally, Init_Win_bytes_backward added 0.7394 to the FTP-Patator score.  

Overall decision: The network traffic was classified as FTP-Patator due to the cumulative effect of these contributing factors increasing the predicted score.
```

### aud2-048

```
The model classified this flow as DDoS. The most influential factors were: 1. act_data_pkt_fwd increased the DDoS score (magnitude 2.7415); 2. Init_Win_bytes_forward increased the DDoS score (magnitude 1.4088); 3. Total Backward Packets increased the DDoS score (magnitude 1.1466); 4. Fwd Packet Length Max increased the DDoS score (magnitude 0.6766); 5. Flow IAT Min increased the DDoS score (magnitude 0.6231).
```

### aud2-049

```
The model classified this flow as SSH-Patator. The most influential factors were: 1. Init_Win_bytes_forward increased the SSH-Patator score (magnitude 5.2456); 2. Init_Win_bytes_backward increased the SSH-Patator score (magnitude 4.4060); 3. URG Flag Count increased the SSH-Patator score (magnitude 3.8950); 4. min_seg_size_forward increased the SSH-Patator score (magnitude 1.0442); 5. Bwd Packets/s increased the SSH-Patator score (magnitude 0.9203).
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-025` to `aud2-049`, in one fenced block.