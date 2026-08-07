# Extractor audit — annotation chunk 03 of 12

You are annotating explanation texts about network-traffic classification. Read
each text and report **what the text itself claims**. Nothing else about this
task is relevant, and no other context is needed.

## Task

For every item, output one record listing **every feature the text makes a
directional claim about**, and the direction the text asserts:

- `"+"`  the text says the feature raises / pushes up the score for the predicted class
- `"-"`  the text says the feature lowers / pushes down that score
- `"unclear"` the text names the feature but commits to no direction

Also set `"hedged": true` when the text gives a direction but softens it
("may slightly reduce", "possibly raises").

## Rules

1. Report **only what the prose says**. Do not judge whether the text is right
   about the traffic. Do not add features the text does not discuss.
2. Use the **canonical feature name** from the vocabulary below, even when the
   text paraphrases it ("maximum forward packet length" -> `Fwd Packet Length Max`).
3. A feature the text does not mention is simply **left out** of the record.
   Do not emit `"absent"` rows.
4. If a text mentions no feature at all, emit `"claims": []` for that item.
5. Output **one JSON object per line** (JSONL), one line per item, in the given
   order, inside a single fenced code block. No commentary before or after.

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
SHAP attribution (top-5) for class Web Attack: Fwd IAT Min=+5.9870; Max Packet Length=+4.7825; Flow IAT Min=+1.5609; Flow Duration=-1.4422; min_seg_size_forward=+0.6789
```

### aud2-051

```
Explanation:  
The classification as **DoS** is supported by the following features:

- **Init_Win_bytes_backward** increases the DoS score. This feature indicates the server's initial TCP window size, and a value of -1 suggests the destination never completed a handshake, which is typical of unanswered or refused probes—common in DoS attacks.
  
- **Idle Min** increases the DoS score. A shorter idle gap between bursts of activity can signal rapid, repeated attempts to probe or overwhelm a system, which aligns with DoS behavior.

- **Idle Mean** increases the DoS score. A long, regular idle period between bursts may indicate periodic beaconing or keep-alive commands, which are often used in sustained DoS attacks to maintain persistent connections.

- **Bwd
```

### aud2-052

```
Explanation:  
The highest contributing factor was Max Packet Length, which increased the FTP-Patator score by 6.3059. Next, Bwd Header Length also increased the score by 5.8738. Fwd Packet Length Std contributed by increasing the score by 3.3831. Packet Length Std further increased the score by 1.0632. Finally, Init_Win_bytes_backward added 0.7394 to the FTP-Patator score.  

Overall decision: The network traffic was classified as FTP-Patator due to the cumulative effect of these contributing factors increasing the predicted score.
```

### aud2-053

```
The traffic in question exhibits characteristics strongly aligned with benign behavior, as evidenced by several key features that collectively support the classification. The client's initial TCP window size, **Init_Win_bytes_forward**, is notably high, which increases the BENIGN score and suggests a proper handshake and normal tool behavior, typical of legitimate traffic. This is further reinforced by the **Bwd Packet Length Min**, which also increases the BENIGN score; its value indicates minimal-only replies from the destination, consistent with acknowledgment or rejection traffic without payload, a pattern often seen in non-malicious interactions. Meanwhile, the **Fwd Packet Length Max**, another feature that raises the BENIGN score, shows a relatively small maximum packet size from the source, pointing to the absence of large data transfers and aligning with control or scan
```

### aud2-054

```
The model predicts the class as **BENIGN**, supported by the following features:

- **Total Backward Packets** increases the BENIGN score. This suggests a balanced flow of packets between source and destination, indicating normal, bidirectional communication rather than one-sided attack traffic.
- **Init_Win_bytes_backward** increases the BENIGN score. A valid TCP handshake is typically observed here, as a value of -1 indicates the destination completed the handshake, which is typical of legitimate network interactions.
- **Fwd Packet Length Max** increases the BENIGN score. A smaller maximum packet size suggests minimal payload transmission, which is characteristic of control-only or scan traffic, often seen in benign network behavior.
- **Active Min** increases the BENIGN score. Brief active transmission periods are typical of single
```

### aud2-055

```
The flow was classified as **BENIGN** due to its low traffic volume and lack of suspicious flag activity. The **PSH Flag Count = 1.0** (low) and **RST Flag Count = 0.0**, **SYN Flag Count = 0.0**, and **FIN Flag Count = 0.0** indicate no signs of connection establishment or termination anomalies. Additionally, the **Flow Duration = 74,156,559.0** and **Flow Packets/s = 0.539** suggest a slow, steady data transfer typical of normal network behavior.
```

### aud2-056

```
The flow was classified as **Web Attack** due to the presence of **PSH Flag Count = 1.0**, which suggests potential payload transmission, and **Subflow Fwd Packets = 3.0**, indicating fragmented or multi-packet behavior often seen in web-based attacks. Additionally, **Bwd Header Length = 40.0** and **Fwd Header Length = 104.0** suggest unusual header sizes, which may indicate malicious payload encapsulation. These features, combined with the overall flow duration and packet distribution, contributed to the classification.
```

### aud2-057

```
Explanation:  
The highest contributing factor was Fwd IAT Min, which significantly increased the Web Attack score by 6.9986. Next, Max Packet Length also increased the score by 4.8000. Flow IAT Min added 2.0446 to the score. Init_Win_bytes_backward contributed 1.1793 to the Web Attack score. Finally, Flow Duration increased the score by 0.9591.  
Overall decision: The network flow was classified as a Web Attack due to the cumulative impact of these contributing factors.
```

### aud2-058

```
Explanation:  
The classification as **DoS** is supported by the following features:

- **Init_Win_bytes_backward** increases the DoS score. This feature indicates the server's initial TCP window size, and a value of -1 suggests the destination never completed a handshake, which is typical of unanswered or refused probes—common in DoS attacks.
  
- **Idle Min** increases the DoS score. A shorter idle gap between bursts of activity can signal rapid, repeated attempts to establish connections, which is characteristic of probing behavior seen in DoS scenarios.

- **Idle Mean** increases the DoS score. A long, regular idle period between bursts may indicate periodic beaconing or keep-alive commands, which are often used in sustained DoS attacks to maintain persistent connections.

- **FIN
```

### aud2-059

```
The traffic in question was classified as a denial-of-service (DoS) attack due to a pattern of behavior that aligns closely with the characteristics of an HTTP flood attack. The server's initial TCP window size, as indicated by the **Init_Win_bytes_backward** feature, was unusually high, which increased the DoS score. This suggests that the destination system was not completing the handshake, a common sign of unanswered or refused probes, often seen in DoS scenarios. The **Idle Min** and **Idle Mean** features both contributed to the DoS score, with **Idle Min** showing a particularly short interval between bursts of activity, indicating rapid resumption of traffic after periods of inactivity. This pattern is typical of coordinated attacks that attempt to overwhelm a system by maintaining frequent, high-volume
```

### aud2-060

```
SHAP attribution (top-5) for class SSH-Patator: Init_Win_bytes_forward=+5.2139; Init_Win_bytes_backward=+4.3976; URG Flag Count=+3.8950; min_seg_size_forward=+1.0277; Bwd Packets/s=+0.9086
```

### aud2-061

```
The flow was classified as **FTP-Patator** due to several key features indicating automated brute-force attempts. A **high PSH Flag Count (1.0)** suggests payload data transmission, common in FTP attempts. The **low Average Packet Size (12.54)** and **low Packet Length Mean (12.04)** indicate small, frequent packets typical of scanning or brute-force behavior. Additionally, the **high Flow Duration (7,996,309 ms)** and **high Bwd IAT Std (1,112,185.57)** suggest irregular, prolonged activity consistent with automated credential guessing.
```

### aud2-062

```
The traffic in question closely aligns with the class profile of PortScan, as it exhibits characteristics consistent with reconnaissance probing across multiple ports. The high Total Length of Foward Packets indicates a significant volume of data being sent from the source to the destination, which is a hallmark of aggressive scanning or exfiltration behavior. This feature increases the PortScan score, reinforcing the suspicion of an active scan. Complementing this is the elevated PSH Flag Count, which suggests a pattern of scripted, small-packet exchanges—common in automated probing attempts, further increasing the PortScan score. Meanwhile, the Bwd Packets/s rate is relatively low, indicating an imbalance in the traffic flow where the destination is not responding actively, which is typical of one-sided attack traffic and thus increases the PortScan score
```

### aud2-063

```
The model predicts the class **DoS** based on the following features, each of which contributes to increasing the DoS score:

1. **Init_Win_bytes_backward**: This feature increases the DoS score. A high value suggests the destination never completed a handshake, which is typical of unanswered or refused probes—behavior commonly associated with DoS attacks.

2. **Idle Mean**: This feature increases the DoS score. A long, regular idle period between activity bursts is characteristic of periodic beaconing or keep-alive command channels, which can be indicative of sustained, coordinated attack traffic.

3. **Init_Win_bytes_forward**: This feature increases the DoS score. An unusual or fixed value here may indicate a crafted traffic pattern, such as those used in DoS attacks, where the client
```

### aud2-064

```
The flow was classified as **DoS** due to several anomalous features. A **high Flow IAT Max** and **Fwd IAT Max** (both 97,400,000.0) indicate extremely long intervals between packets, suggesting potential flooding or slow-rate attacks. Additionally, **Bwd Header Length** is unusually high at 232.0, which may indicate abnormal protocol behavior. The **Flow Duration** is also extremely long (97,400,465.0), further supporting the presence of a sustained, potentially malicious traffic pattern.
```

### aud2-065

```
Explanation:  
The classification as **SSH-Patator** is supported by several key features that align with the behavior of this intrusion type.  

- **Bwd Header Length** increases the SSH-Patator score. This is because a higher value suggests header-only reply streams, which are characteristic of acknowledgment or reset traffic without content—common in automated probing or scanning activities typical of SSH-Patator.  
- **Total Length of Bwd Packets** increases the SSH-Patator score. This feature highlights near-zero replies against non-trivial forward traffic, indicating unanswered probes or refused services, which are hallmarks of brute-force attempts seen in SSH-Patator attacks.  
- **Fwd Packet Length Std** increases the SSH-Patator score. A near-zero deviation in forward packet
```

### aud2-066

```
The model predicts the class **DDoS** based on the following features, each of which contributes to increasing the DDoS score:

1. **act_data_pkt_fwd**: This feature increases the DDoS score. A non-zero value indicates that forward packets carry actual payload data, suggesting active data transfer rather than simple probing or handshake-only behavior, which is characteristic of DDoS traffic.

2. **Init_Win_bytes_backward**: This feature increases the DDoS score. A positive value indicates the server's initial TCP window size, which is typically larger in DDoS scenarios where the attacker establishes a connection and sends data, as opposed to unanswered or refused probes.

3. **Fwd Packet Length Max**: This feature increases the DDoS score. A larger maximum packet length suggests
```

### aud2-067

```
SHAP attribution (top-5) for class Bot: Init_Win_bytes_backward=+5.0289; Init_Win_bytes_forward=+3.5115; Fwd Header Length=+1.9376; Flow Bytes/s=+1.0307; Fwd Packets/s=+0.5474
```

### aud2-068

```
This flow was classified as **SSH-Patator** due to several key features indicating automated, repetitive SSH brute-force attempts. The **Bwd Header Length** being extremely high (1032.0) suggests large, possibly malformed packets typical of automated tools. The **Bwd IAT Std** and **Bwd IAT Total** values are unusually high, indicating long, irregular intervals between packets, a hallmark of brute-force attacks. Additionally, the **PSH Flag Count** is 1.0, suggesting packet segmentation, often used in automated login attempts. These features collectively point to a pattern consistent with SSH-Patator.
```

### aud2-069

```
The predicted class is **SSH-Patator**, supported by the following features:

- **Init_Win_bytes_forward** increases the SSH-Patator score. This feature reflects the client's initial TCP window size, which in crafted traffic often has unusual fixed values, indicating a tool-driven pattern typical of SSH-Patator.
- **Init_Win_bytes_backward** increases the SSH-Patator score. This represents the server's initial TCP window size, and a value of -1 suggests the destination did not complete a handshake, a common characteristic of unanswered probes associated with SSH-Patator.
- **URG Flag Count** increases the SSH-Patator score. The presence of non-zero URG flags in both directions is anomalous in modern benign traffic, suggesting deliberate manipulation consistent with SSH-P
```

### aud2-070

```
The flow was classified as **PortScan** due to high **Bwd Packets/s** (34,482.76) and **Flow Packets/s** (68,965.52), indicating a high rate of packets sent in a short time, which is typical of scanning behavior. Additionally, **PSH Flag Count = 1.0** suggests push flags were used, often seen in scanning activities. The **Flow Duration = 29.0** and **Flow IAT Std = 0.0** indicate a consistent, rapid sequence of packets, further supporting the PortScan classification.
```

### aud2-071

```
The traffic in question was flagged as a **Web Attack** due to a combination of anomalous network behaviors that align with the characteristics of layered web-based exploits. The initial TCP window size on the client side, **Init_Win_bytes_forward**, was unusually high, which increased the Web Attack score—this is a strong indicator of crafted traffic, as such values are often associated with tools or stacks that attempt to fingerprint the network in a non-standard way. Complementing this, the server's initial TCP window size, **Init_Win_bytes_backward**, was also atypical, further increasing the score—this suggests a lack of proper handshake completion, a common sign of probing or scanning activity. The presence of a non-zero **URG Flag Count**, which increased the score, points to unusual TCP
```

### aud2-072

```
The traffic in question closely aligns with the class profile of PortScan, a pattern characterized by reconnaissance probing across many ports, often involving many short, small, one-sided flows. This behavior is evident through several key features that collectively contribute to the classification. The **Total Length of Foward Packets** is notably high, which increases the PortScan score, suggesting a large volume of data being sent from the source to the destination—potentially indicating a bulk upload or exfiltration phase, though in this case, the pattern seems more exploratory. Alongside this, the **Flow IAT Mean** is also elevated, further increasing the score, as a very small mean time between consecutive packets suggests a highly regular and possibly automated flow, consistent with scripted probing. The **Flow IAT Min
```

### aud2-073

```
The model predicts **Web Attack** based on the following features:

- **Fwd IAT Min** increases the Web Attack score. This feature indicates the shortest gap in the source's sending, and a near-zero value suggests packet bursts, which are characteristic of attack tools attempting to overwhelm a system.

- **Max Packet Length** increases the Web Attack score. A small maximum packet size implies the flow never carried real data, which is often seen in malicious traffic attempting to avoid detection or carry minimal payload.

- **Flow IAT Min** increases the Web Attack score. This feature reflects the shortest gap between consecutive packets, and a near-zero value indicates back-to-back packet bursts, a sign of flooding behavior typical in web attacks.

- **Flow Duration** decreases the Web Attack score. An unusually short
```

### aud2-074

```
The prediction of **FTP-Patator** is supported by the following features, each of which contributes to increasing the FTP-Patator score:

1. **Total Length of Fwd Packets**: This feature increases the FTP-Patator score. A very large total length indicates bulk data transfer, which is characteristic of automated brute-force attacks like FTP-Patator, where large volumes of data are sent during credential attempts.

2. **Fwd PSH Flags**: This feature also increases the FTP-Patator score. The frequent setting of PSH (Push) flags by the source suggests a pattern of sending small packets rapidly, typical of interactive or automated credential-stuffing tools used in FTP-Patator attacks.

3. **Fwd Packet Length Std**: This feature increases the FTP-P
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-050` to `aud2-074`, in one fenced block.