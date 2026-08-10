# Extractor audit — annotation chunk 10 of 12

You are annotating explanation texts about network-traffic classification. Read
each text and report **what the text itself claims**. No other context is needed
and none is relevant.

## Task

For each item, list **every feature the text makes a directional claim about**,
and the direction the text asserts:

- `"+"` — the text says the feature raises / pushes up the score for the class it argues for
- `"-"` — the text says it lowers / pushes down that score
- `"unclear"` — the text names the feature but commits to no direction

Set `"hedged": true` when a direction is softened ("may slightly reduce").

## Rules

1. Report **only what the prose says**, not whether it is correct about the traffic.
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


### aud2-225

```
The model classified this flow as PortScan. The most influential factors were: 1. Total Length of Fwd Packets increased the PortScan score (magnitude 2.1036); 2. Bwd Packets/s increased the PortScan score (magnitude 1.2072); 3. Init_Win_bytes_forward increased the PortScan score (magnitude 1.1976); 4. PSH Flag Count increased the PortScan score (magnitude 1.0046); 5. Flow Duration increased the PortScan score (magnitude 0.7669).
```

### aud2-226

```
The model predicts the class **DoS** based on the following features, each of which contributes to increasing the DoS score:

1. **Init_Win_bytes_backward**: This feature increases the DoS score. A value of -1 indicates that the destination never completed a handshake, which is typical of unanswered or refused probes—a behavior commonly associated with Denial of Service attacks.

2. **Idle Min**: This feature increases the DoS score. A shorter idle gap suggests rapid resumption of activity between bursts, which can indicate frequent and coordinated probing behavior, often seen in DoS scenarios.

3. **Idle Mean**: This feature increases the DoS score. A long mean idle gap between activity bursts is characteristic of periodic beaconing or keep-alive command channels, which are often used in sustained
```

### aud2-227

```
SHAP attribution (top-5) for class SSH-Patator: Init_Win_bytes_forward=+5.0303; Init_Win_bytes_backward=+4.4092; URG Flag Count=+3.8950; min_seg_size_forward=+1.0347; Bwd Packets/s=+0.8035
```

### aud2-228

```
Explanation:  
The classification as DDoS is supported by several key features that indicate abnormal traffic patterns consistent with distributed denial-of-service attacks.  

- **act_data_pkt_fwd** increases the DDoS score because it reflects forward packets carrying actual payload data, suggesting active data transfer rather than mere probing or handshake-only behavior, which is common in DDoS attacks.  
- **Bwd Packet Length Mean** increases the DDoS score as near-zero values can indicate responses to unanswered scan probes, a pattern often seen in coordinated attack traffic.  
- **Init_Win_bytes_forward** increases the DDoS score because unusual fixed values for the client's initial TCP window size may reveal crafted traffic, such as that generated by malicious tools or bots.  
- **Fwd Packet Length Max
```

### aud2-229

```
SHAP attribution (top-5) for class DoS: Init_Win_bytes_forward=+2.7883; Average Packet Size=+1.1829; Bwd Packets/s=+1.1344; Fwd Packets/s=+1.1151; Flow IAT Max=+0.5386
```

### aud2-230

```
The model classified this flow as BENIGN. The most influential factors were: 1. Init_Win_bytes_backward increased the BENIGN score (magnitude 1.8985); 2. Total Backward Packets increased the BENIGN score (magnitude 0.9371); 3. Fwd Packet Length Max increased the BENIGN score (magnitude 0.6910); 4. Active Min increased the BENIGN score (magnitude 0.5358); 5. Average Packet Size increased the BENIGN score (magnitude 0.4578).
```

### aud2-231

```
Explanation:  
The highest contributing factor was Fwd IAT Min, which significantly increased the Web Attack score by 6.3516. Next, Max Packet Length also increased the score by 4.7387. Flow Duration had a moderate decreasing effect on the score, reducing it by 1.4443. Flow IAT Min contributed to the increase with a smaller magnitude of 1.3158. Finally, Init_Win_bytes_backward slightly decreased the score by 0.8767.  
Overall decision: The model predicted a Web Attack based on the cumulative effect of these features, with the most significant contributors being Fwd IAT Min and Max Packet Length.
```

### aud2-232

```
Explanation:  
The Total Length of Fwd Packets significantly increased the FTP-Patator score by 4.1582.  
Fwd PSH Flags further increased the FTP-Patator score by 4.0821.  
Fwd Packet Length Std added to the FTP-Patator score with a magnitude of 2.5015.  
Init_Win_bytes_forward contributed to the FTP-Patator score by 1.3521.  
Packet Length Std also increased the FTP-Patator score by 1.2594.  

Overall decision: The network traffic was classified as FTP-Patator due to the cumulative effect of these contributing factors.
```

### aud2-233

```
Explanation:  
The classification as a **Web Attack** is supported by several key features that align with the characteristics of such attacks.  

- **Fwd IAT Min** is high, indicating near-zero gaps between consecutive packets from the source. This suggests packet bursts, a common behavior in automated attack tools.  
- **Max Packet Length** is large, implying that the flow did not carry real data, which is typical of malicious traffic attempting to overwhelm or probe the network.  
- **Flow IAT Min** is low, showing back-to-back packet bursts, a hallmark of flooding attacks that aim to saturate network resources.  
- **Init_Win_bytes_backward** is negative, meaning the destination did not complete a TCP handshake. This is often seen in unanswered probes or refused connections,
```

### aud2-234

```
The predicted class is **BENIGN**, supported by the following features:

- **Init_Win_bytes_forward** increases the BENIGN score. This feature reflects the client's initial TCP window size, which is often fixed in tool or stack fingerprints. A properly established handshake would set this value, indicating normal, non-malicious traffic.

- **Init_Win_bytes_backward** increases the BENIGN score. This represents the server's initial TCP window size. A value of -1 suggests the destination did not complete a handshake, which is typical of unanswered probes or refused connections—behavior consistent with benign scanning or probing activity.

- **Average Packet Size** increases the BENIGN score. A smaller average packet size is characteristic of control or probe traffic, which is often associated with benign network behavior such as
```

### aud2-235

```
The model classified this flow as SSH-Patator. The most influential factors were: 1. Init_Win_bytes_forward increased the SSH-Patator score (magnitude 5.0303); 2. Init_Win_bytes_backward increased the SSH-Patator score (magnitude 4.4092); 3. URG Flag Count increased the SSH-Patator score (magnitude 3.8950); 4. min_seg_size_forward increased the SSH-Patator score (magnitude 1.0347); 5. Bwd Packets/s increased the SSH-Patator score (magnitude 0.8035).
```

### aud2-236

```
The traffic in question exhibits characteristics that align closely with normal, non-malicious behavior, as indicated by the features contributing to the BENIGN classification. The high value of Total Backward Packets suggests a significant amount of communication from the destination to the source, which is typical of legitimate, two-way interactions rather than one-sided attack patterns. This is further reinforced by the elevated Init_Win_bytes_backward, indicating that the destination completed a proper TCP handshake, which is a hallmark of normal network behavior rather than unanswered or refused probes. The Fwd Packet Length Max, being relatively large, implies that the source was sending substantial data packets, consistent with regular data transfer rather than minimal or scan-like activity. Meanwhile, the Active Min feature shows brief but consistent activity periods, suggesting that the traffic was initiated and
```

### aud2-237

```
The model predicts the class as **BENIGN**, supported by the following features:

1. **Init_Win_bytes_backward** increases the BENIGN score. This feature reflects the server's initial TCP window size, with a value of -1 indicating a failed handshake, typical of unanswered probes. Such behavior is consistent with benign traffic patterns where connections are initiated but not fully established.

2. **Total Backward Packets** increases the BENIGN score. This feature counts the number of packets sent from the destination to the source. Asymmetry in packet flow, such as a higher number of backward packets, can indicate one-sided communication, which is often observed in benign traffic where responses are minimal or non-existent.

3. **Fwd Packet Length Max** increases the BENIGN score. This feature
```

### aud2-238

```
The traffic in question was flagged as a **Web Attack** due to a combination of behavioral patterns that align closely with known indicators of malicious activity at the web layer. The flow began with a **Fwd IAT Min** value that significantly increased the Web Attack score, suggesting a burst of packets from the source, a hallmark of automated attack tools attempting to overwhelm the target. This was further reinforced by a **Max Packet Length** that also increased the score, indicating that the flow never carried substantial data, which is typical of probing or scanning behavior rather than legitimate communication. The **Flow IAT Min** followed suit, contributing to the score with a near-zero minimum interval between packets, a sign of back-to-back bursts that are characteristic of flood attacks. Meanwhile, the **Init_Win_bytes_backward
```

### aud2-239

```
The traffic in question exhibits characteristics strongly aligned with Botnet command-and-control activity, as evidenced by several key features that collectively paint a picture of automated, coordinated, and potentially malicious behavior. The high value of **Init_Win_bytes_backward**, which increases the Bot score, suggests that the server's initial TCP window size was unusually large, a sign of a crafted or automated connection, possibly indicating a refused or unanswered probe, a common behavior in botnet probing. This is further reinforced by **Init_Win_bytes_forward**, also increasing the Bot score, which points to a client-side configuration with unusual fixed values, often indicative of a tool fingerprint or a stack that is being used to generate traffic in a non-standard way, such as in automated scans or bot-driven communication. The **Fwd Header Length
```

### aud2-240

```
Explanation:  
The classification as **BENIGN** is supported by several features that align with characteristics of normal, controlled network traffic.  

- **Init_Win_bytes_forward** increases the BENIGN score. This feature reflects the client's initial TCP window size, which is often set to standard values in normal traffic. Unusual or fixed values can indicate crafted traffic, but the presence of a typical value here suggests a legitimate connection.  
- **Init_Win_bytes_backward** also increases the BENIGN score. This represents the server's initial TCP window size. A value of -1 would indicate a failed handshake, but the absence of such a value suggests a completed and normal handshake, typical of benign activity.  
- **Average Packet Size** increases the BENIGN score. Smaller average packet
```

### aud2-241

```
The predicted class is **SSH-Patator**, supported by the following features:

1. **Init_Win_bytes_forward** increases the SSH-Patator score. This feature reflects the client's initial TCP window size, which in crafted traffic often has unusual fixed values, indicating a tool-driven pattern typical of SSH-Patator.

2. **Init_Win_bytes_backward** increases the SSH-Patator score. This represents the server's initial TCP window size, and a value of -1 suggests the destination did not complete a handshake, a common characteristic of unanswered probes associated with SSH-Patator.

3. **URG Flag Count** increases the SSH-Patator score. The presence of non-zero URG flags in both directions is anomalous in modern benign traffic, suggesting deliberate manipulation of
```

### aud2-242

```
Explanation:  
The classification as **DoS** is supported by the following features:

- **Init_Win_bytes_backward** increases the DoS score. This feature indicates the server's initial TCP window size, and a value of -1 suggests the destination never completed a handshake, which is typical of unanswered or refused probes—common in DoS attacks.
  
- **Idle Min** increases the DoS score. A shorter idle gap between bursts of activity can signal rapid, repeated attempts to probe or overwhelm a system, which aligns with DoS behavior.

- **Idle Mean** increases the DoS score. A long, regular idle period between bursts may indicate periodic beaconing or keep-alive commands, which are often used in sustained DoS attacks to maintain persistent connections.

- **Bwd
```

### aud2-243

```
Explanation:  
1. High Init_Win_bytes_backward significantly increased the BENIGN score, indicating a benign initiation of data transfer.  
2. A large number of Total Backward Packets further boosted the BENIGN score, suggesting normal traffic patterns.  
3. Fwd Packet Length Max contributed positively to the BENIGN score, reflecting consistent forward packet sizes.  
4. Active Min added to the BENIGN score, showing stable minimum active connections.  
5. Average Packet Size also increased the BENIGN score, aligning with typical benign communication patterns.  

Overall decision: The network activity is classified as BENIGN based on the cumulative positive contributions of these features.
```

### aud2-244

```
Explanation:  
The classification as a **Web Attack** is supported by several key features that align with the characteristics of such attacks.  

- **Fwd IAT Min** is high, indicating near-zero gaps between consecutive packets from the source. This suggests packet bursts, a common behavior in automated attack tools.  
- **Max Packet Length** is large, implying that the flow did not carry real data, which is typical of malicious traffic attempting to overwhelm or probe the network.  
- **Flow IAT Min** is low, showing back-to-back packet bursts, a hallmark of flooding attacks that aim to saturate network resources.  
- **Init_Win_bytes_backward** is negative, meaning the destination did not complete a TCP handshake. This is often seen in unanswered probes or refused connections,
```

### aud2-245

```
SHAP attribution (top-5) for class BENIGN: Init_Win_bytes_forward=+1.8362; Init_Win_bytes_backward=+1.3149; Average Packet Size=+0.7303; Fwd Header Length=+0.3048; Packet Length Std=+0.2792
```

### aud2-246

```
Explanation:  
1. High Init_Win_bytes_backward significantly increased the DDoS score by 1.5499, indicating abnormal initial window bytes in the backward direction.  
2. Increased act_data_pkt_fwd further raised the DDoS score by 1.3816, suggesting a higher rate of data packets forwarded in active connections.  
3. Elevated Bwd Packet Length Mean added 1.3386 to the DDoS score, pointing to larger average packet lengths in the backward direction.  
4. A high Fwd Packet Length Max contributed 1.3085 to the DDoS score, showing unusually large forward packet lengths.  
5. Increased Packet Length Mean added 0.6241 to the DDoS
```

### aud2-247

```
The model classified this flow as SSH-Patator. The most influential factors were: 1. Init_Win_bytes_forward increased the SSH-Patator score (magnitude 5.1597); 2. Init_Win_bytes_backward increased the SSH-Patator score (magnitude 4.3209); 3. URG Flag Count increased the SSH-Patator score (magnitude 3.8427); 4. min_seg_size_forward increased the SSH-Patator score (magnitude 0.9662); 5. Bwd Packets/s increased the SSH-Patator score (magnitude 0.7307).
```

### aud2-248

```
The predicted class is **BENIGN**, supported by the following features:

- **Max Packet Length** increases the BENIGN score. A small maximum packet size suggests the flow did not carry substantial data, which is typical of benign traffic.
- **Packet Length Std** increases the BENIGN score. Near-zero variability in packet sizes indicates uniform, machine-generated packets, a characteristic often seen in benign network behavior.
- **Init_Win_bytes_forward** increases the BENIGN score. A fixed, unusual value for the initial TCP window size may indicate a proper handshake, which is common in legitimate traffic.
- **Bwd Packets/s** increases the BENIGN score. A low backward packet rate relative to a high forward rate suggests one-sided communication, which is typical of benign flows rather than attack traffic
```

### aud2-249

```
Explanation:  
1. High values in `act_data_pkt_fwd` significantly increased the DDoS score by 1.5998.  
2. Elevated `Init_Win_bytes_backward` further increased the DDoS score by 1.3344.  
3. A large `Fwd Packet Length Max` contributed to the DDoS score with a magnitude of 1.2650.  
4. The `Total Length of Fwd Packets` also increased the DDoS score by 1.2297.  
5. However, higher `Init_Win_bytes_forward` slightly decreased the DDoS score by 0.6668.  

The model predicted DDoS based on the cumulative impact of these
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-225` to `aud2-249`, in one fenced block.