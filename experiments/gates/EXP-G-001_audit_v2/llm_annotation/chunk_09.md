# Extractor audit — annotation chunk 09 of 12

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


### aud2-200

```
The flow was classified as **DoS** due to several anomalous features. A **high Flow Duration** (85,203,080.0) and **high Bwd IAT Max** (85,100,000.0) suggest prolonged, unusual activity. The **low Fwd Packet Length Mean** (53.83) and **high Bwd Packet Length Mean** (1,656.43) indicate asymmetric data flow, common in DoS attacks. Additionally, **zero ACK Flag Count** and **zero PSH Flags** in both directions suggest abnormal TCP behavior, further supporting the DoS classification.
```

### aud2-201

```
The flow was classified as **FTP-Patator** due to several key features indicating automated brute-force attempts. A **SYN Flag Count = 1.0** suggests initiation of a connection, while **Fwd PSH Flags = 1.0** and **Fwd Packets/s = 11834.31953** indicate rapid data transmission, typical of password guessing. Additionally, **FIN Flag Count = 0.0** and **PSH Flag Count = 0.0** suggest sustained connection attempts, aligning with FTP-Patator's behavior of repeatedly attempting login credentials.
```

### aud2-202

```
The model predicts the class **Bot** based on the following features, each of which contributes to increasing the Bot score:

- **Init_Win_bytes_backward** indicates the server's initial TCP window size. A value of -1 suggests the destination never completed a handshake, which is typical of unanswered or refused probes—common in Bot-related traffic.
- **Init_Win_bytes_forward** reflects the client's initial TCP window size. Unusual or fixed values here may signal crafted traffic, such as that used in Bot networks, where improper handshakes are often observed.
- **Fwd Header Length** measures the total TCP/IP header bytes in the forward direction. A high header-to-payload ratio is associated with control-heavy traffic, such as scans or floods, which are characteristic of Bot activity.
```

### aud2-203

```
The model's prediction of **PortScan** is supported by several key features that align with the behavior patterns associated with this class.

- **Total Length of Fwd Packets** increases the PortScan score. This feature reflects the total bytes sent from the source to the destination. A high value suggests bulk data transfer, which can be indicative of scanning activity where large amounts of data are sent during probing or exfiltration phases.

- **PSH Flag Count** also increases the PortScan score. The PSH (Push) flag in TCP indicates urgency in data transmission. A higher count of PSH flags, especially on small packets, suggests scripted or automated request-response exchanges, which are commonly observed in scanning activities.

- **Bwd Packets/s** increases the PortScan score. This feature
```

### aud2-204

```
Explanation:  
The highest contributing factor was Max Packet Length, which increased the BENIGN score by 0.7253. Next, Packet Length Std also increased the BENIGN score by 0.5666. Then, Init_Win_bytes_forward raised the BENIGN score by 0.4744. Following this, Bwd Packets/s contributed to the BENIGN score with an increase of 0.4197. Finally, Fwd Header Length added to the BENIGN score with an increase of 0.4112.  

Overall decision: The network traffic is classified as BENIGN based on the cumulative positive contributions from these features.
```

### aud2-205

```
The flow was classified as **DDoS** due to high **Down/Up Ratio (2.0)**, indicating an imbalance between incoming and outgoing traffic, a common sign of DDoS attacks. Additionally, the **Flow Duration (1,078,095.0)** and **Bwd IAT Total (1,078,058.0)** suggest prolonged and sustained traffic, typical of sustained DDoS activity. The **Bwd Header Length (152.0)** and **Bwd Packet Length Std (1942.88)** also point to irregular and potentially malicious traffic patterns.
```

### aud2-206

```
Explanation:  
The classification as **BENIGN** is supported by several features that align with characteristics of normal, controlled network traffic.  

- **Init_Win_bytes_forward** increases the BENIGN score. This feature reflects the client's initial TCP window size, which is often set to standard values in normal traffic. Unusual or fixed values can indicate crafted traffic, but the presence of a typical value here suggests a legitimate handshake.  
- **Init_Win_bytes_backward** also increases the BENIGN score. This represents the server's initial TCP window size. A value of -1 would indicate a failed handshake, but the absence of such a value suggests a completed connection, typical of benign activity.  
- **Average Packet Size** increases the BENIGN score. A smaller average packet size is
```

### aud2-207

```
Explanation:  
The classification as **PortScan** is supported by several key features.  

- **Total Length of Fwd Packets** increases the PortScan score, as very large totals suggest bulk data transfer, which is often associated with scanning or exfiltration activities.  
- **Bwd Packets/s** also increases the score, reflecting a low backward packet rate compared to a high forward rate, which indicates one-sided traffic typical of scanning behavior.  
- **Init_Win_bytes_forward** raises the score, as unusual or fixed initial window sizes can signal crafted traffic, such as that seen in automated scanning tools.  
- **PSH Flag Count** contributes positively, as elevated counts on small packets suggest scripted request-response exchanges, commonly observed during port scans.  
- **Flow Duration
```

### aud2-208

```
Explanation:  
1. High Init_Win_bytes_backward significantly increased the Bot score by 4.9112.  
2. High Init_Win_bytes_forward further increased the Bot score by 3.1358.  
3. Increased Fwd Header Length added 1.9376 to the Bot score.  
4. Elevated Flow Bytes/s contributed 0.9953 to the Bot score.  
5. Longer Flow Duration added 0.4396 to the Bot score.  

The combination of these factors led to the prediction of **Bot**.
```

### aud2-209

```
Explanation:  
The classification as **SSH-Patator** is supported by several key features that align with the behavior of this intrusion-detection class.  

- **Init_Win_bytes_forward** increases the SSH-Patator score. This feature reflects the client's initial TCP window size, which is often set to unusual values in crafted traffic, such as in SSH-Patator attacks, to fingerprint the tool or bypass standard handshakes.  
- **Init_Win_bytes_backward** also increases the score. This represents the server's initial TCP window size, and a value of -1 typically indicates that the destination did not complete a handshake, a common pattern in unanswered or refused probes associated with automated scanning tools like SSH-Patator.  
- **URG Flag Count** raises the score
```

### aud2-210

```
The traffic in question was flagged as Bot due to a pattern of features that collectively suggest the presence of automated, coordinated, or malicious network behavior. The initial server-side TCP window size, **Init_Win_bytes_backward**, was unusually high, which increased the Bot score and points to a potential refusal or incomplete handshake, a common sign of probing or scanning activity. This is further supported by the **Init_Win_bytes_forward**, which also increased the Bot score, indicating a client-side configuration that may be non-standard or crafted, often seen in botnet traffic where the client's behavior is controlled or manipulated. The **Fwd Header Length** was also elevated, contributing to the Bot score, and this suggests a high header-to-payload ratio, which is characteristic of control-heavy traffic such as scans or
```

### aud2-211

```
The network behavior observed aligns with the **Bot** class due to the following features:

- **Init_Win_bytes_backward** increases the Bot score. This feature indicates the server's initial TCP window size, and a value of -1 suggests the destination never completed a handshake, which is typical of unanswered or refused probes—common in bot-driven traffic.

- **Bwd IAT Std** increases the Bot score. This feature reflects the jitter in the destination's reply timing. Abnormal regularity or gaps in timing suggest scripted exchanges rather than organic user sessions, which is characteristic of bot activity.

- **Init_Win_bytes_forward** increases the Bot score. This feature represents the client's initial TCP window size. Unusual or fixed values here can reveal crafted traffic, as they may indicate a
```

### aud2-212

```
The traffic in question was classified as a DDoS attack due to a pattern of behavior that aligns closely with the class profile of distributed denial-of-service attacks, which are characterized by volumetric traffic from many sources. The evidence begins with the **Bwd Packet Length Mean**, which increased the DDoS score—this suggests that the responses from the destination were unusually small, potentially indicating a flood of unanswered scan probes, a common sign of probing activity in a DDoS attack. Supporting this, the **Packet Length Mean** also increased the score, pointing to an overall trend of smaller packet sizes, which is typical of control or probe traffic rather than data transfer, further reinforcing the idea of a coordinated scan or attack. The **Init_Win_bytes_backward** feature, which also increased the
```

### aud2-213

```
The traffic in question was flagged as a denial-of-service (DoS) attack due to a pattern of behavior that aligns closely with the characteristics of an HTTP flood. The server's initial TCP window size, as indicated by the **Init_Win_bytes_backward** feature, was unusually high, which increased the DoS score. This suggests that the connection was not properly established, a common sign of unanswered or refused probes, often seen in DoS attacks where the server is overwhelmed with incomplete handshakes. The **Idle Min** and **Idle Mean** features both contributed to the DoS score, with **Idle Min** indicating that the shortest idle gap between bursts of activity was unusually short, and **Idle Mean** showing that the average idle time between bursts was also low. This pattern of
```

### aud2-214

```
Explanation:  
1. High Init_Win_bytes_forward increased the BENIGN score by 1.8362.  
2. High Init_Win_bytes_backward further increased the BENIGN score by 1.3149.  
3. Large Average Packet Size added to the BENIGN score with a magnitude of 0.7303.  
4. Elevated Fwd Header Length contributed to the BENIGN score by 0.3048.  
5. High Packet Length Std slightly increased the BENIGN score by 0.2792.  

Overall decision: The network traffic was classified as BENIGN due to consistently high values across key benign-indicative features.
```

### aud2-215

```
The model classified this flow as FTP-Patator. The most influential factors were: 1. Total Length of Fwd Packets increased the FTP-Patator score (magnitude 4.1656); 2. Fwd PSH Flags increased the FTP-Patator score (magnitude 3.6462); 3. Fwd Packet Length Std increased the FTP-Patator score (magnitude 2.7371); 4. Packet Length Std decreased the FTP-Patator score (magnitude 1.3427); 5. Init_Win_bytes_forward increased the FTP-Patator score (magnitude 1.2817).
```

### aud2-216

```
Explanation:  
The classification as DDoS is supported by several key features.  

- **Init_Win_bytes_backward** increases the DDoS score, as a value of -1 indicates the destination never completed a handshake, which is typical of unanswered or refused probes often seen in DDoS attacks.  
- **act_data_pkt_fwd** increases the DDoS score, since a value of zero suggests a flow that only involved handshakes or probes and never sent data, a pattern commonly associated with scanning or probing behavior in DDoS scenarios.  
- **Bwd Packet Length Mean** increases the DDoS score, as near-zero values for backward packets can indicate unanswered scan probes, a sign of network scanning activity often linked to DDoS.  
- **Fwd
```

### aud2-217

```
The traffic in question closely aligns with the class profile of FTP-Patator, a brute-force credential guessing attack against an FTP server. The evidence points to a coordinated attempt to exhaustively guess valid login credentials through repeated, systematically varied packet exchanges. The largest contributing factor was the **Max Packet Length**, which increased the FTP-Patator score—suggesting that the flow involved relatively large packets, indicative of actual data transfer rather than minimal header-only traffic, which would be typical of a small or non-functional connection. This implies the attack was not just a probe but an active attempt to interact with the server. The **Bwd Header Length** also increased the score, pointing to a pattern of header-only responses in the backward direction, which is characteristic of automated or machine-generated traffic, such as
```

### aud2-218

```
The model's prediction of **PortScan** is supported by several key features, each contributing to the likelihood of this class based on their directional impact on the score:

- **Total Length of Fwd Packets** increases the PortScan score. This feature reflects the total bytes sent from the source to the destination. Large values suggest bulk data transfer, which is often associated with scanning activities where probes are sent to map network resources.
  
- **Init_Win_bytes_forward** increases the PortScan score. This feature indicates the client's initial TCP window size, which can reveal crafted traffic patterns. Unusual or fixed values may signal a lack of proper handshake, common in automated scanning behavior.

- **PSH Flag Count** increases the PortScan score. A higher count of PSH flags in both
```

### aud2-219

```
Explanation:  
The classification as **Bot** is supported by the following features:

- **Init_Win_bytes_backward** increases the Bot score. This feature indicates the server's initial TCP window size, and a value of -1 suggests the destination never completed a handshake, which is typical of unanswered or refused probes—common in botnet activity.

- **Bwd IAT Min** increases the Bot score. A near-zero value for the shortest gap between destination replies suggests rapid-fire responses, such as rejection storms, which are often seen in botnet traffic.

- **Flow IAT Max** increases the Bot score. A large gap between consecutive packets indicates idle-and-resume behavior, which is characteristic of keep-alive or command-and-control channels used by bots.

- **Fwd IAT Max
```

### aud2-220

```
This flow was classified as **SSH-Patator** due to several key features indicating automated, repetitive SSH brute-force attempts. The **Bwd Header Length** being extremely high (1032.0) suggests large, possibly malformed packets typical of automated tools. The **Flow Duration** is very long (12,443,684.0 seconds), and **Bwd IAT Std** is very high (812,361.8186), indicating irregular and prolonged intervals between packets, a hallmark of brute-force attacks. Additionally, the **PSH Flag Count** is 1.0, suggesting packet segmentation, often used in automated credential guessing. These features collectively point to a sustained, automated SSH attack pattern.
```

### aud2-221

```
The model predicts the class **Bot** based on the following features, each of which contributes to increasing the Bot score:

- **Init_Win_bytes_backward** indicates the server's initial TCP window size. A value of -1 suggests the destination never completed a handshake, which is typical of unanswered or refused probes—common in Bot-related traffic.
- **Init_Win_bytes_forward** reflects the client's initial TCP window size. Unusual or fixed values here may signal crafted traffic, such as that used in Bot networks, where improper handshakes are often observed.
- **Fwd Header Length** measures the total TCP/IP header bytes in the forward direction. A high header-to-payload ratio is associated with control-heavy traffic, such as scans or floods, which are characteristic of Bot activity.
```

### aud2-222

```
The predicted class is **BENIGN**, supported by the following features:

- **Init_Win_bytes_forward** increases the BENIGN score. This feature reflects the client's initial TCP window size, which is often set to standard values in normal, properly established connections. A fixed, unusual value can indicate crafted traffic, but in this case, the presence of a proper handshake (non-zero value) suggests benign behavior.

- **Init_Win_bytes_backward** increases the BENIGN score. This feature represents the server's initial TCP window size. A value of -1 would indicate a failed handshake, but the presence of a valid value suggests a normal, initiated connection, aligning with benign traffic.

- **Average Packet Size** increases the BENIGN score. A smaller average packet size is typical of
```

### aud2-223

```
The flow was classified as **Bot** due to high **Bwd Packets/s** (33333.33) and **Flow Packets/s** (66666.67), indicating a high rate of packets in both directions, which is unusual for normal traffic. Additionally, the **Flow Duration** of 30 seconds with **Flow IAT Std**, **Fwd IAT Std**, and **Bwd IAT Std** all at 0.0 suggests a highly consistent and potentially automated packet timing, common in botnet activity. The **URG Flag Count** being 1.0 may also indicate urgent or abnormal traffic patterns.
```

### aud2-224

```
The model predicts the class **Bot** based on the following features, each of which contributes to increasing the Bot score:

1. **Init_Win_bytes_backward**: This feature increases the Bot score. A value of -1 indicates the destination never completed a handshake, which is typical of unanswered or refused probes—behavior commonly associated with Bot activity.

2. **Bwd IAT Std**: This feature increases the Bot score. Abnormal regularity or gaps in the destination's reply timing suggest scripted exchanges rather than organic sessions, a pattern often seen in Bot-driven traffic.

3. **Init_Win_bytes_forward**: This feature increases the Bot score. A fixed or unusual value here may indicate a stack or tool fingerprint, revealing crafted traffic. Values of 0 or -1 suggest no proper handshake,
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-200` to `aud2-224`, in one fenced block.