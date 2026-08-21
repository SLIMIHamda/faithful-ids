# Extractor audit — annotation chunk 03 of 03

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


### aud2-050

```
SHAP attribution (top-5) for class SSH-Patator: Bwd Header Length=+4.8244; Total Length of Bwd Packets=+4.3185; Fwd Packet Length Std=+1.1687; Fwd Packet Length Max=+1.0569; min_seg_size_forward=+0.9677
```

### aud2-051

```
Explanation:  
1. A high value in Init_Win_bytes_forward significantly increased the DoS score by 3.1715.  
2. Fwd Packets/s further increased the DoS score by 1.4065.  
3. Average Packet Size contributed to the DoS score with an increase of 1.1822.  
4. Bwd Packets/s added to the DoS score, increasing it by 1.0944.  
5. Flow IAT Min also raised the DoS score by 0.7456.  

The combination of these factors led to the prediction of a DoS attack.
```

### aud2-052

```
The model classified this flow as FTP-Patator. The most influential factors were: 1. Max Packet Length increased the FTP-Patator score (magnitude 6.3059); 2. Bwd Header Length increased the FTP-Patator score (magnitude 5.8738); 3. Fwd Packet Length Std increased the FTP-Patator score (magnitude 3.3756); 4. Packet Length Std increased the FTP-Patator score (magnitude 1.1028); 5. Init_Win_bytes_backward increased the FTP-Patator score (magnitude 0.7394).
```

### aud2-053

```
Explanation:  
1. High Init_Win_bytes_backward significantly increased the DoS score by 3.0045.  
2. A long Idle Min further increased the DoS score by 0.9849.  
3. A high Idle Mean also contributed to the DoS score by 0.9684.  
4. Elevated Bwd Packet Length Std added to the DoS score with a magnitude of 0.7922.  
5. A notable FIN Flag Count increased the DoS score by 0.6434.  

The model predicted **DoS** based on the cumulative impact of these contributing factors.
```

### aud2-054

```
The model classified this flow as PortScan. The most influential factors were: 1. Total Length of Fwd Packets increased the PortScan score (magnitude 2.0936); 2. Init_Win_bytes_forward increased the PortScan score (magnitude 1.2529); 3. Flow Bytes/s increased the PortScan score (magnitude 1.1337); 4. PSH Flag Count increased the PortScan score (magnitude 1.0112); 5. Packet Length Mean increased the PortScan score (magnitude 0.6916).
```

### aud2-055

```
The flow was classified as **BENIGN** due to its low traffic volume and lack of suspicious flags. The **Flow Duration** of 1404.0 seconds and **Flow Packets/s** of 2849.0 suggest a steady, controlled data transfer. Additionally, **Bwd Packets/s** and **Fwd Packets/s** are both high, indicating balanced bidirectional communication. The absence of **SYN**, **FIN**, **RST**, or **PSH** flags, along with low **ACK Flag Count**, suggests no abrupt connection termination or retransmission, further supporting a benign classification.
```

### aud2-056

```
The model classified this flow as DDoS. The most influential factors were: 1. act_data_pkt_fwd increased the DDoS score (magnitude 1.8005); 2. Bwd Packet Length Mean increased the DDoS score (magnitude 1.7010); 3. Init_Win_bytes_forward increased the DDoS score (magnitude 1.0361); 4. Fwd Packet Length Max increased the DDoS score (magnitude 0.8815); 5. Init_Win_bytes_backward increased the DDoS score (magnitude 0.7416).
```

### aud2-057

```
SHAP attribution (top-5) for class DoS: Init_Win_bytes_forward=+3.1595; Fwd Packets/s=+1.4043; Average Packet Size=+1.1826; Bwd Packets/s=+1.0940; Flow IAT Min=+0.7441
```

### aud2-058

```
Explanation:  
The Total Length of Fwd Packets significantly increased the PortScan score by 2.1038.  
The Flow IAT Mean further increased the PortScan score by 1.1835.  
The Flow IAT Min also increased the PortScan score by 1.0859.  
The Init_Win_bytes_forward contributed to the increase by 1.0777.  
The PSH Flag Count added a smaller increase of 1.0242 to the PortScan score.  

Overall decision: The network flow was classified as PortScan due to the cumulative effect of these contributing factors.
```

### aud2-059

```
The flow was classified as **DDoS** due to its unusually long **Flow Duration** (8,001,793.0) and **Flow IAT Std** (4,618,963.55), indicating irregular and potentially malicious timing patterns. The **Fwd Packets/s** and **Flow Packets/s** are very low (0.5), suggesting a slow but sustained attack, while **Active Max**, **Idle Max**, and **Fwd IAT Max** are extremely high, pointing to prolonged idle periods typical in DDoS attacks. Additionally, the **Fwd Header Length** is high (80.0), which may indicate abnormal packet structures often seen in distributed attacks.
```

---

Now output exactly 10 JSONL lines, one per item above, from `aud2-050` to `aud2-059`, in one fenced block.