# Extractor audit — annotation chunk 04 of 12

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


### aud2-075

```
The model classified this flow as DoS. The most influential factors were: 1. Init_Win_bytes_forward increased the DoS score (magnitude 1.9851); 2. Bwd Packets/s increased the DoS score (magnitude 1.2003); 3. Average Packet Size increased the DoS score (magnitude 1.0177); 4. Fwd Packets/s increased the DoS score (magnitude 0.5589); 5. Fwd IAT Mean increased the DoS score (magnitude 0.4325).
```

### aud2-076

```
The flow was classified as **PortScan** due to high **Bwd Packets/s** (23,255.81) and **Flow Packets/s** (46,511.63), indicating a high rate of packets sent in a short time, which is typical of scanning behavior. Additionally, **PSH Flag Count = 1.0** suggests push flags were used, often seen in scanning activities. The **Flow Duration = 43.0** and **Flow IAT Std = 0.0** indicate a consistent, rapid sequence of packets, further supporting the PortScan classification.
```

### aud2-077

```
Explanation:  
1. A high value in Init_Win_bytes_forward significantly increased the SSH-Patator score by 5.2139.  
2. A high value in Init_Win_bytes_backward further increased the SSH-Patator score by 4.3976.  
3. A high count of URG Flags increased the SSH-Patator score by 3.8950.  
4. A larger min_seg_size_forward increased the SSH-Patator score by 1.0277.  
5. A higher Bwd Packets/s increased the SSH-Patator score by 0.9086.  

Overall decision: The network activity strongly indicates an SSH-Patator attack based on the cumulative contribution of these features
```

### aud2-078

```
The flow was classified as **PortScan** due to high **Bwd Packets/s** (21,276.59) and **Flow Packets/s** (42,553.19), indicating a high rate of packets sent in a short time, typical of scanning behavior. The **Flow Duration** (47.0) and **Flow IAT Mean** (47.0) suggest a single, rapid burst of traffic, consistent with scanning. Additionally, the **PSH Flag Count** (1.0) and **Fwd Packet Length Mean** (0.0) indicate small, frequent packets, further supporting the PortScan classification.
```

### aud2-079

```
Explanation:  
1. High Init_Win_bytes_forward significantly increased the DoS score by 1.9851.  
2. Elevated Bwd Packets/s further increased the DoS score by 1.2003.  
3. Larger Average Packet Size contributed to the DoS score with a magnitude of 1.0177.  
4. Increased Fwd Packets/s added to the DoS score by 0.5589.  
5. Higher Fwd IAT Mean slightly boosted the DoS score by 0.4325.  

The combination of these factors led to the prediction of a DoS attack.
```

### aud2-080

```
The flow was classified as **PortScan** due to high **Bwd Packets/s** (20,000.0) and **Flow Packets/s** (40,000.0), indicating a high rate of packets sent in a short time, which is typical of scanning behavior. Additionally, **PSH Flag Count** is 1.0, suggesting attempts to push data, often seen in scanning activities. The **Flow Duration** of 50.0 seconds and **Flow IAT Std** of 0.0 indicate a consistent, rapid sequence of packets, further supporting the PortScan classification.
```

### aud2-081

```
Explanation:  
1. The act_data_pkt_fwd value increased the DDoS score by 1.6010, indicating a strong contribution to the detection of a DDoS attack.  
2. The Init_Win_bytes_backward value further increased the DDoS score by 1.4036, reinforcing the likelihood of a DDoS attack.  
3. The Bwd Packet Length Mean increased the DDoS score by 1.3349, adding to the evidence supporting the prediction.  
4. The Fwd Packet Length Max increased the DDoS score by 1.3013, contributing to the overall assessment.  
5. The Total Length of Bwd Packets increased the DDoS score by 0.6
```

### aud2-082

```
The flow was classified as **DDoS** due to high **Flow Duration** (98,822.0) and **Flow Packets/s** (70.83), indicating a prolonged and high-rate network activity. The **Down/Up Ratio** of 2.0 suggests more data being sent downstream, which is common in DDoS attacks. Additionally, the **Bwd IAT Std** (41,088.38) and **Bwd IAT Total** (98,734.0) show irregular and extended intervals between packets in the backward direction, further supporting the DDoS classification.
```

### aud2-083

```
The flow was classified as **Web Attack** due to high **Bwd Packets/s** (50,000.0) and **Fwd Packets/s** (50,000.0), indicating a high rate of packets in both directions, which is suspicious. Additionally, the **Bwd Header Length** is 32.0, which is unusually high for typical web traffic, suggesting potential malicious payload handling. These features point toward a high-speed, possibly automated or bot-driven activity, aligning with a **Web Attack** classification.
```

### aud2-084

```
The model predicts the class **Bot** based on the following features, each of which increases the Bot score:

1. **Init_Win_bytes_backward**: This feature indicates the server's initial TCP window size. A value of -1 suggests the destination never completed a handshake, which is typical of unanswered or refused probes—common in Bot-related traffic.

2. **Init_Win_bytes_forward**: This reflects the client's initial TCP window size. Unusual or fixed values here can reveal crafted traffic, such as that generated by Botnets, where no proper handshake occurs, indicated by values of 0 or -1.

3. **Fwd Header Length**: This measures the total TCP/IP header bytes in the forward direction. A high header-to-payload ratio is indicative of control-heavy traffic, such
```

### aud2-085

```
The model predicts the class **DoS** based on the following features, each of which contributes to increasing the DoS score:

1. **Init_Win_bytes_forward**: This feature indicates the client's initial TCP window size. Unusual or fixed values here may signal a crafted traffic pattern, which is often associated with malicious activity such as denial-of-service attacks. Such values can reveal a lack of proper handshake, pointing toward an attempt to overwhelm the target system.

2. **Fwd Packets/s**: A high rate of packets sent from the source suggests aggressive scanning or flooding behavior, both of which are characteristic of DoS attacks. This feature reflects a potential overload on the network from the client side.

3. **Average Packet Size**: A smaller average packet size may indicate control or probe traffic
```

### aud2-086

```
The model's prediction of **Bot** is supported by several key features that align with behaviors typical of botnet activity:

- **Flow IAT Max** increases the Bot score. This feature captures the longest gap between consecutive packets, which is indicative of idle-and-resume behavior often seen in keep-alive or command-and-control channels, both of which are common in botnet communications.
  
- **Bwd IAT Min** also increases the Bot score. This reflects the shortest gap between destination replies, and near-zero values suggest rapid-fire responses, such as those seen in rejection storms, which are often used by bots to overwhelm systems.

- **Packet Length Mean** increases the Bot score. The average packet size being small suggests control or probe traffic, which is characteristic of botnet activity where initial
```

### aud2-087

```
Explanation:  
The classification as **FTP-Patator** is supported by several key features that align with the behavior of this intrusion type.  

- **Max Packet Length** increases the FTP-Patator score. A large maximum packet size suggests the flow carried real data, which is consistent with active FTP attempts where data is transferred.  
- **Bwd Header Length** increases the FTP-Patator score. A high value here indicates header-only traffic in the backward direction, which may represent reset or acknowledgment packets, common in automated FTP probing.  
- **Fwd Packet Length Std** increases the FTP-Patator score. Low variability in forward packet sizes suggests uniform, machine-generated packets, a hallmark of automated tools like FTP-Patator used for brute-force attacks.  
- **Packet
```

### aud2-088

```
The model predicts **Web Attack** based on the following features, each of which increases the Web Attack score:

1. **Init_Win_bytes_forward**: This feature indicates the client's initial TCP window size. Unusual fixed values here suggest crafted traffic, which is often associated with malicious activity, as such values may reveal stack or tool fingerprints used in attacks.

2. **Init_Win_bytes_backward**: This reflects the server's initial TCP window size. A value of -1 typically indicates that the destination did not complete a handshake, which is common in unanswered or refused probes—behavior typical of probing or scanning activities.

3. **URG Flag Count**: The presence of any non-zero count of TCP URG flags in both directions is anomalous in modern benign traffic. This suggests potential malicious intent
```

### aud2-089

```
The traffic in question was flagged as a **Web Attack** due to a combination of behavioral patterns that align closely with known indicators of malicious activity at the web layer. The flow began with a **Fwd IAT Min** value that significantly increased the Web Attack score, suggesting a burst of packets from the source, a hallmark of automated attack tools attempting to overwhelm the target. This was further reinforced by a **Max Packet Length** that also increased the score, indicating that the flow never carried substantial data, which is typical of probing or scanning behavior rather than legitimate communication. The **Flow IAT Min** followed suit, contributing to the score with a near-zero minimum gap between packets, a sign of back-to-back bursts that are characteristic of flood attacks. Meanwhile, the **Init_Win_bytes_backward
```

### aud2-090

```
Explanation:  
1. High Init_Win_bytes_forward increased the BENIGN score by 2.3657.  
2. High Init_Win_bytes_backward further increased the BENIGN score by 0.5813.  
3. High Average Packet Size added to the BENIGN score with a magnitude of 0.5402.  
4. High Packet Length Std contributed to the BENIGN score, adding 0.2516.  
5. High Fwd Header Length also increased the BENIGN score by 0.2288.  

The combination of these factors led to the prediction of BENIGN.
```

### aud2-091

```
The model classified this flow as Bot. The most influential factors were: 1. Init_Win_bytes_backward increased the Bot score (magnitude 4.9112); 2. Init_Win_bytes_forward increased the Bot score (magnitude 3.1358); 3. Fwd Header Length increased the Bot score (magnitude 1.9376); 4. Flow Bytes/s increased the Bot score (magnitude 0.9953); 5. Flow Duration increased the Bot score (magnitude 0.4396).
```

### aud2-092

```
The traffic in question was flagged as a **Web Attack** due to a combination of behavioral patterns that align closely with known indicators of malicious activity at the web layer. The most significant contributing factor was **Fwd IAT Min**, which increased the Web Attack score by a large magnitude, suggesting a bursty transmission pattern typical of automated attack tools attempting to overwhelm a service with rapid, coordinated packets. This aligns with the behavior seen in SQL injection or cross-site scripting attacks, where attackers often send packets in quick succession to exploit vulnerabilities. Supporting this pattern was **Max Packet Length**, which also increased the score, indicating that the flow never carried substantial data, a sign that the communication was likely probing or attempting to inject malicious payloads rather than transferring meaningful content. Meanwhile, **Flow Duration** had a smaller
```

### aud2-093

```
Explanation:  
1. High Init_Win_bytes_backward significantly increased the Bot score by 5.0289.  
2. High Init_Win_bytes_forward further increased the Bot score by 3.5115.  
3. Increased Fwd Header Length added 1.9376 to the Bot score.  
4. Elevated Flow Bytes/s contributed 1.0307 to the Bot score.  
5. Higher Fwd Packets/s added 0.5474 to the Bot score.  

The model predicted **Bot** based on the cumulative impact of these contributing factors.
```

### aud2-094

```
The traffic in question was flagged as a **Web Attack** due to a combination of behavioral patterns that align closely with known indicators of malicious activity at the web layer. The flow began with a **Fwd IAT Min** value that significantly increased the Web Attack score, suggesting a burst of packets from the source, a hallmark of automated attack tools attempting to overwhelm the target. This was further reinforced by a **Max Packet Length** that also increased the score, indicating that the flow never carried substantial data, which is typical of probing or scanning behavior rather than legitimate communication. The **Flow IAT Min** followed suit, contributing to the score with a near-zero minimum gap between packets, a sign of back-to-back bursts that are characteristic of flood attacks. Meanwhile, the **Init_Win_bytes_backward
```

### aud2-095

```
The network flow is classified as a **Web Attack** due to several key features that align with the characteristics of malicious traffic:

- **Init_Win_bytes_forward** increases the Web Attack score. This feature reflects the client's initial TCP window size, which is often set to unusual values in crafted traffic. Such values can indicate a stack or tool fingerprint, suggesting non-standard or malicious behavior.

- **Init_Win_bytes_backward** also increases the Web Attack score. This represents the server's initial TCP window size. A value of -1 typically indicates that the destination did not complete a handshake, which is common in unanswered or refused probes—behavior often associated with scanning or probing activities.

- **URG Flag Count** raises the Web Attack score. The presence of any non-zero count of TCP U
```

### aud2-096

```
Explanation:  
1. High Init_Win_bytes_forward significantly increased the SSH-Patator score by 5.1597.  
2. High Init_Win_bytes_backward further increased the SSH-Patator score by 4.3209.  
3. Elevated URG Flag Count contributed to the SSH-Patator score with a magnitude of 3.8427.  
4. Larger min_seg_size_forward added to the SSH-Patator score by 0.9662.  
5. Increased Bwd Packets/s slightly raised the SSH-Patator score by 0.7307.  

The decision to classify the connection as SSH-Patator is driven by the cumulative effect of these contributing factors, all of which increased
```

### aud2-097

```
The model predicts **Web Attack** based on the following features, each of which contributes to increasing the Web Attack score:

- **Fwd IAT Min**: Near-zero values suggest packet bursts, a hallmark of attack tools attempting to overwhelm the network.
- **Max Packet Length**: Small maxima indicate the flow never carried real data, which is characteristic of malicious traffic attempting to evade detection.
- **Flow IAT Min**: Near-zero minima indicate back-to-back packet bursts, a sign of flood-like behavior typical in web attacks.
- **Init_Win_bytes_backward**: A value of -1 means the destination never completed a handshake, which is common in unanswered or refused probes, often associated with probing or scanning activities.
- **min_seg_size_forward**: Constant minimal values suggest uniform crafted packets from
```

### aud2-098

```
The flow was classified as **BENIGN** due to its low flag activity and stable packet behavior. The absence of suspicious flags like ACK, PSH, URG, or RST (all at 0.0) suggests minimal control-plane activity. Additionally, the low variability in packet lengths (standard deviation of 29.76) and consistent segment sizes indicate normal, steady data transfer. These features align with benign traffic patterns.
```

### aud2-099

```
Explanation:  
1. High Init_Win_bytes_forward significantly increased the DoS score by 2.7883.  
2. Larger Average Packet Size further increased the DoS score by 1.1829.  
3. Elevated Bwd Packets/s contributed to the DoS score with an increase of 1.1344.  
4. Increased Fwd Packets/s added to the DoS score, raising it by 1.1151.  
5. A higher Flow IAT Max also contributed, increasing the DoS score by 0.5386.  

The decision to classify the traffic as DoS is driven by the cumulative impact of these factors, each of which increased the DoS score.
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-075` to `aud2-099`, in one fenced block.