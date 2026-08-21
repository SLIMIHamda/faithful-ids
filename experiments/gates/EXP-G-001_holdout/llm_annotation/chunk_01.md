# Extractor audit — annotation chunk 01 of 03

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


### aud2-000

```
Explanation:  
1. A high value in Init_Win_bytes_forward significantly increased the SSH-Patator score by 5.2456.  
2. A high value in Init_Win_bytes_backward further increased the SSH-Patator score by 4.4060.  
3. A high count of URG Flags increased the SSH-Patator score by 3.8950.  
4. A larger min_seg_size_forward increased the SSH-Patator score by 1.0442.  
5. A higher Bwd Packets/s increased the SSH-Patator score by 0.9203.  

Overall decision: The network activity strongly indicates an SSH-Patator attack based on the cumulative contribution of these features
```

### aud2-001

```
Explanation:  
1. High Init_Win_bytes_backward increased the BENIGN score by 1.8986.  
2. A large number of Total Backward Packets further increased the BENIGN score by 1.0733.  
3. Fwd Packet Length Max contributed to the BENIGN score with an increase of 0.6455.  
4. Active Min also increased the BENIGN score by 0.6024.  
5. Fwd IAT Std added to the BENIGN score with an increase of 0.4211.  

The decision favors BENIGN based on these contributing factors.
```

### aud2-002

```
SHAP attribution (top-5) for class DoS: Init_Win_bytes_backward=+2.8856; Idle Min=+1.0224; Idle Mean=+0.9044; FIN Flag Count=+0.7171; Bwd Packet Length Std=+0.7091
```

### aud2-003

```
Explanation:  
The Total Length of Fwd Packets significantly increased the PortScan score by 2.1011.  
The Init_Win_bytes_forward further increased the score by 1.0857.  
The Bwd Packets/s also contributed by increasing the score by 1.0750.  
The PSH Flag Count added to the score with a magnitude of 1.0241.  
The Flow Bytes/s increased the score by 0.8046.  
The cumulative effect of these factors led to the prediction of PortScan.
```

### aud2-004

```
Explanation:  
The Total Length of Fwd Packets significantly increased the PortScan score by 2.0936.  
The Init_Win_bytes_forward further increased the PortScan score by 1.2529.  
The Flow Bytes/s contributed to the PortScan score with an increase of 1.1337.  
The PSH Flag Count added to the PortScan score, increasing it by 1.0112.  
The Packet Length Mean also raised the PortScan score by 0.6916.  

Overall decision: The network flow was classified as PortScan due to the cumulative increase in the PortScan score from these contributing factors.
```

### aud2-005

```
SHAP attribution (top-5) for class BENIGN: Init_Win_bytes_forward=+2.3657; Init_Win_bytes_backward=+0.5813; Average Packet Size=+0.5402; Packet Length Std=+0.2516; Fwd Header Length=+0.2288
```

### aud2-006

```
SHAP attribution (top-5) for class Bot: Init_Win_bytes_backward=+4.9280; Init_Win_bytes_forward=+3.1784; Fwd Header Length=+1.9376; Flow IAT Mean=-0.9125; Flow Bytes/s=+0.8479
```

### aud2-007

```
SHAP attribution (top-5) for class BENIGN: Init_Win_bytes_forward=+2.2500; Bwd Packet Length Min=+1.0519; Fwd Packet Length Max=+0.6535; Idle Min=-0.3133; Init_Win_bytes_backward=+0.2692
```

### aud2-008

```
Explanation:  
1. High Init_Win_bytes_backward significantly increased the DoS score by 2.3553.  
2. Elevated Idle Mean further increased the DoS score by 1.1049.  
3. Increased Init_Win_bytes_forward added to the DoS score with a magnitude of 1.0896.  
4. Greater Bwd Packet Length Std contributed to the DoS score by 0.9875.  
5. Higher Idle Min also raised the DoS score by 0.9104.  

The model predicted **DoS** based on the cumulative impact of these contributing factors.
```

### aud2-009

```
Explanation:  
1. A high Bwd Header Length significantly increased the SSH-Patator score by 4.8244.  
2. A large Total Length of Bwd Packets further increased the SSH-Patator score by 4.3148.  
3. A high Fwd Packet Length Std contributed to the SSH-Patator score with an increase of 1.1604.  
4. A high Fwd Packet Length Max added to the SSH-Patator score with an increase of 1.0569.  
5. A high min_seg_size_forward also increased the SSH-Patator score by 0.9651.  

The model predicts the connection is **SSH-Patator** due to the cumulative
```

### aud2-010

```
The model classified this flow as FTP-Patator. The most influential factors were: 1. Max Packet Length increased the FTP-Patator score (magnitude 6.3059); 2. Bwd Header Length increased the FTP-Patator score (magnitude 5.8738); 3. Fwd Packet Length Std increased the FTP-Patator score (magnitude 3.4219); 4. Packet Length Std increased the FTP-Patator score (magnitude 1.0442); 5. Init_Win_bytes_backward increased the FTP-Patator score (magnitude 0.7394).
```

### aud2-011

```
The flow was classified as **FTP-Patator** due to several key features indicating automated brute-force attempts. A **high PSH Flag Count (1.0)** suggests payload negotiation, common in FTP attempts. **High Bwd Header Length (488.0)** and **high Fwd Header Length (296.0)** indicate large header sizes typical of FTP traffic. Additionally, **low Average Packet Size (12.125)** and **low Avg Fwd Segment Size (11.444)** align with small data transfers seen in brute-force attacks. These features collectively point to automated FTP login attempts.
```

### aud2-012

```
The model classified this flow as DDoS. The most influential factors were: 1. act_data_pkt_fwd increased the DDoS score (magnitude 1.6010); 2. Init_Win_bytes_backward increased the DDoS score (magnitude 1.4036); 3. Bwd Packet Length Mean increased the DDoS score (magnitude 1.3349); 4. Fwd Packet Length Max increased the DDoS score (magnitude 1.3013); 5. Total Length of Bwd Packets increased the DDoS score (magnitude 0.6188).
```

### aud2-013

```
The flow was classified as **DoS** due to high **Flow IAT Std** and **Flow IAT Max**, indicating highly variable intervals between packets, which is common in distributed denial-of-service attacks. The **Flow Duration** and **Flow IAT Max** suggest an unusually long session with irregular timing, potentially masking malicious traffic. Additionally, the **Bwd Header Length** and **Fwd Header Length** being unusually high may indicate abnormal packet structures often seen in DoS attacks.
```

### aud2-014

```
Explanation:  
The Total Length of Fwd Packets significantly increased the FTP-Patator score by 4.1656.  
Fwd PSH Flags further increased the FTP-Patator score by 3.6462.  
Fwd Packet Length Std added to the FTP-Patator score with a magnitude of 2.7371.  
Packet Length Std slightly decreased the FTP-Patator score by 1.3427.  
Init_Win_bytes_forward contributed to the FTP-Patator score with a magnitude of 1.2817.  

Overall decision: The network traffic was classified as FTP-Patator due to the cumulative effect of these contributing factors.
```

### aud2-015

```
Explanation:  
The highest contributing factor was Fwd IAT Min, which significantly increased the Web Attack score by 7.2361. Next, Max Packet Length also increased the score by 4.7808. Flow IAT Min further raised the score by 2.1648. Init_Win_bytes_backward added 1.0627 to the score. Finally, Flow Duration contributed an additional 0.8855.  
Overall decision: The network flow was classified as a Web Attack due to the cumulative increase in the Web Attack score from these key features.
```

### aud2-016

```
The flow was classified as **DoS** due to extremely high **Fwd Packets/s** and **Fwd Packets/s** values, indicating a massive rate of packets being sent in the forward direction, which is a common sign of a denial-of-service attack. The **Flow Packets/s** value of 666,666.67 suggests an abnormally high traffic rate, overwhelming the target system. Additionally, the **Fwd Packets/s** and **Fwd IAT Mean** values are unusually high, further supporting the detection of a potential DoS attack.
```

### aud2-017

```
The model classified this flow as DDoS. The most influential factors were: 1. act_data_pkt_fwd increased the DDoS score (magnitude 2.9255); 2. Init_Win_bytes_forward increased the DDoS score (magnitude 1.3944); 3. Total Backward Packets increased the DDoS score (magnitude 1.1495); 4. Flow IAT Min increased the DDoS score (magnitude 0.6869); 5. Fwd Packet Length Max increased the DDoS score (magnitude 0.6766).
```

### aud2-018

```
Explanation:  
1. The act_data_pkt_fwd value significantly increased the DDoS score by 1.8005.  
2. The Bwd Packet Length Mean further increased the DDoS score by 1.7010.  
3. The Init_Win_bytes_forward contributed to the DDoS score with an increase of 1.0361.  
4. The Fwd Packet Length Max added to the DDoS score with an increase of 0.8815.  
5. The Init_Win_bytes_backward also increased the DDoS score by 0.7416.  

Overall decision: The network traffic was classified as DDoS due to the cumulative effect of these contributing factors.
```

### aud2-019

```
The flow was classified as **FTP-Patator** due to several key features indicating automated, repetitive brute-force attempts. A **high PSH Flag Count (1.0)** suggests payload negotiation, common in FTP. **High Bwd Header Length (488.0)** and **high Fwd Header Length (296.0)** indicate large headers, often used to bypass rate limits. Additionally, **low Average Packet Size (11.95)** and **low Avg Fwd Segment Size (11.0)** suggest small, frequent data transfers typical of automated login attempts. These features align with FTP-Patator's behavior of sending many small packets in rapid succession.
```

### aud2-020

```
Explanation:  
The Total Length of Fwd Packets significantly increased the PortScan score by 2.0969.  
The Init_Win_bytes_forward further increased the PortScan score by 1.2595.  
The PSH Flag Count contributed to the PortScan score by increasing it by 1.0109.  
The Flow Bytes/s added to the PortScan score with a magnitude of 0.9072.  
The Bwd Packets/s also increased the PortScan score by 0.7932.  

Overall decision: The network flow was classified as PortScan due to the cumulative effect of these contributing factors.
```

### aud2-021

```
The model classified this flow as PortScan. The most influential factors were: 1. Total Length of Fwd Packets increased the PortScan score (magnitude 2.2285); 2. PSH Flag Count increased the PortScan score (magnitude 0.8674); 3. Bwd Packets/s increased the PortScan score (magnitude 0.7822); 4. Flow IAT Mean decreased the PortScan score (magnitude 0.6310); 5. Fwd Packets/s decreased the PortScan score (magnitude 0.4954).
```

### aud2-022

```
SHAP attribution (top-5) for class FTP-Patator: Max Packet Length=+6.3059; Bwd Header Length=+5.8738; Fwd Packet Length Std=+3.3831; Packet Length Std=+1.0632; Init_Win_bytes_backward=+0.7394
```

### aud2-023

```
Explanation:  
1. High Init_Win_bytes_backward significantly increased the Bot score by 4.5495.  
2. Bwd IAT Std further increased the Bot score by 1.4471.  
3. Init_Win_bytes_forward contributed to the Bot score with an increase of 1.2292.  
4. Bwd Packet Length Max added to the Bot score with an increase of 0.9696.  
5. Total Length of Bwd Packets also increased the Bot score by 0.8811.  

The model predicted **Bot** based on the cumulative impact of these contributing factors.
```

### aud2-024

```
The model classified this flow as DDoS. The most influential factors were: 1. Init_Win_bytes_backward increased the DDoS score (magnitude 1.5499); 2. act_data_pkt_fwd increased the DDoS score (magnitude 1.3816); 3. Bwd Packet Length Mean increased the DDoS score (magnitude 1.3386); 4. Fwd Packet Length Max increased the DDoS score (magnitude 1.3085); 5. Packet Length Mean increased the DDoS score (magnitude 0.6241).
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-000` to `aud2-024`, in one fenced block.