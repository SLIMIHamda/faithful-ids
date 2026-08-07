# Extractor audit — annotation chunk 06 of 12

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


### aud2-125

```
The flow was classified as **Bot** due to high **Bwd Packets/s** (25,641.03) and **Flow Packets/s** (51,282.05), indicating a high rate of packets in both directions, which is unusual for normal traffic. Additionally, the **Flow Duration** (39.0) and **Flow IAT Std** (0.0) suggest a very short and consistent interval between packets, typical of automated or bot-driven activity. The **URG Flag Count** (1.0) and **ACK Flag Count** (1.0) also point to potential abnormal signaling behavior.
```

### aud2-126

```
The flow was classified as **FTP-Patator** due to several key features indicating automated brute-force attempts. A **high PSH Flag Count (1.0)** suggests repeated packet segmentation, common in FTP brute-force attacks. Additionally, **low Average Packet Size (12.125)** and **low Avg Fwd Segment Size (11.444)** indicate small, frequent data transfers typical of password guessing. The **high Flow Duration (8,363,935.0)** and **high Bwd IAT Total (8,363,878.0)** suggest prolonged, sustained connection attempts, further aligning with FTP-Patator behavior.
```

### aud2-127

```
The traffic in question closely aligns with the class profile of PortScan, as it exhibits a pattern of reconnaissance probing through many ports, characterized by one-sided flows and minimal interaction. The evidence begins with the **Total Length of Fwd Packets**, which increases the PortScan score—this suggests a large volume of data being sent from the source to the destination, consistent with bulk probing or scanning activity. This is further reinforced by the **Init_Win_bytes_forward**, which also increases the score; its unusual value points to a crafted handshake, a hallmark of automated or malicious tools attempting to fingerprint the target. As the traffic unfolds, the **PSH Flag Count** rises, contributing to the PortScan score—elevated PSH flags on small packets indicate a scripted exchange, typical of probing
```

### aud2-128

```
The traffic in question exhibits characteristics strongly aligned with a denial-of-service (DoS) attack, as evidenced by several key features that collectively point to a coordinated attempt to overwhelm the target system. The initial TCP window size, **Init_Win_bytes_forward**, is unusually high, which increases the DoS score and suggests a crafted or malicious connection setup, possibly indicating a tool or stack fingerprint designed to evade normal handshake behaviors. This unusual value sets the stage for an aggressive flow. Complementing this is the **Average Packet Size**, which is also elevated, further increasing the DoS score and implying a large volume of data being transmitted, consistent with content transfer rather than control or probe traffic. Meanwhile, the **Bwd Packets/s**—the rate of packets from the destination—remains low
```

### aud2-129

```
The traffic in question closely aligns with the class profile of SSH-Patator, a brute-force credential guessing attack against SSH. The evidence begins with **Init_Win_bytes_forward**, which increases the SSH-Patator score by a significant magnitude of 5.2456. This feature reflects the client's initial TCP window size, and its unusual fixed value suggests a crafted handshake, a hallmark of automated tools attempting to fingerprint the target. The **Init_Win_bytes_backward** also increases the score, with a magnitude of 4.4060, indicating the server's initial TCP window size. A value of -1 here is typical of unanswered or refused probes, further supporting the idea of a one-sided attack where the server does not complete the handshake. 

The **UR
```

### aud2-130

```
Explanation:  
The classification as **FTP-Patator** is supported by several key features that align with the behavior of this intrusion type.  

- **Max Packet Length** increases the FTP-Patator score. A large maximum packet size suggests the flow carried real data, which is characteristic of active FTP attempts where data is transferred.  
- **Bwd Header Length** also increases the score. A high value here indicates header-only traffic in the backward direction, which may correspond to reset or acknowledgment packets typical of automated FTP scanning.  
- **Packet Length Std** increases the score. A near-zero standard deviation in packet sizes suggests uniformity, a sign of machine-generated traffic often seen in automated attacks like FTP-Patator.  
- **Average Packet Size** increases the score. A relatively
```

### aud2-131

```
The traffic in question exhibits characteristics strongly aligned with Botnet command-and-control activity, as evidenced by several key features that collectively support the classification as Bot. The presence of a high Flow IAT Max, which increases the Bot score by 2.7810, suggests that there are long gaps between consecutive packets, indicative of idle-and-resume behavior commonly seen in keep-alive or command-and-control channels. This pattern aligns with the behavior of bots waiting for instructions before resuming communication. Complementing this is the Bwd IAT Min, which also increases the Bot score by 2.7558, pointing to near-zero gaps between destination replies, a sign of rapid-fire responses such as those seen in rejection storms or automated feedback loops typical of botnet traffic. Meanwhile
```

### aud2-132

```
Explanation:  
1. High Init_Win_bytes_backward significantly increased the Bot score by 4.3512.  
2. Bwd Packet Length Max further increased the Bot score by 1.6459.  
3. Bwd IAT Std contributed to the Bot score with an increase of 1.1522.  
4. Init_Win_bytes_forward added to the Bot score with an increase of 1.1339.  
5. Total Length of Bwd Packets provided additional support to the Bot score by 0.8933.  

The model predicted **Bot** based on the cumulative impact of these contributing factors.
```

### aud2-133

```
The traffic in question is classified as **BENIGN**, and the evidence points to a pattern consistent with normal, non-malicious behavior. The server's initial TCP window size, **Init_Win_bytes_backward**, is notably high, which increases the BENIGN score and suggests a properly established and stable connection, typical of legitimate communication rather than probing or scanning. This is further supported by the **Total Backward Packets**, which also increases the BENIGN score—indicating a balanced exchange of packets between the source and destination, rather than one-sided traffic that might suggest an attack. The **Fwd Packet Length Max**, another feature that raises the BENIGN score, shows that the largest packets sent by the source are relatively small, which is characteristic of traffic that does not carry large payloads,
```

### aud2-134

```
Explanation:  
The classification as **BENIGN** is supported by several features that indicate normal, non-malicious network behavior.  

- **Total Backward Packets** increases the BENIGN score, suggesting a balanced flow of traffic where both directions are active, rather than one-sided communication typical of attacks.  
- **Init_Win_bytes_backward** increases the BENIGN score, as a valid handshake indicates proper protocol engagement, rather than failed or refused connections often seen in probing attacks.  
- **Fwd Packet Length Max** increases the BENIGN score, implying that the source is sending small packets, which is characteristic of non-malicious traffic such as scans or control signals, rather than large data transfers associated with malicious payloads.  
- **Active Min** increases the BENIGN score
```

### aud2-135

```
The traffic in question closely aligns with the class profile of FTP-Patator, a brute-force credential guessing attack against an FTP server. The evidence points to a coordinated attempt to exhaustively guess valid login credentials through repeated, rapid, and uniform packet transmissions. The **Total Length of Fwd Packets** is notably high, which increases the FTP-Patator score, suggesting a large volume of data being sent from the source, likely in the form of repeated login attempts. This is further reinforced by the **Fwd PSH Flags**, which also increase the score—indicating that the source is pushing data on every small packet, a behavior typical of automated credential-stuffing clients that send login requests in quick succession. The **Fwd Packet Length Std** is very low, again increasing
```

### aud2-136

```
Explanation:  
The classification as **FTP-Patator** is supported by several key features that align with the behavior of this intrusion type.  

- **Total Length of Fwd Packets** increases the FTP-Patator score, indicating a large volume of data being sent from the source to the destination. This is consistent with bulk upload or exfiltration behavior commonly seen in automated attacks like FTP-Patator.  
- **Fwd PSH Flags** also increases the score, reflecting frequent use of the TCP PSH (Push) flag, which is typical of interactive tools and credential-stuffing clients—behavior often observed in brute-force attempts associated with FTP-Patator.  
- **Fwd Packet Length Std** increases the score, showing low variability in packet sizes, a characteristic
```

### aud2-137

```
The model predicts **Web Attack** based on the following features:

- **Fwd IAT Min** increases the Web Attack score. This feature indicates the shortest gap in the source's sending, and near-zero values suggest packet bursts, which are characteristic of attack tools launching rapid, coordinated attacks.

- **Max Packet Length** increases the Web Attack score. A small maximum packet size implies the flow never carried real data, which is often seen in malicious traffic where packets are crafted to evade detection or carry minimal payload for scanning or probing.

- **Flow IAT Min** increases the Web Attack score. This feature reflects the shortest gap between consecutive packets, and near-zero minima indicate back-to-back packet bursts, a hallmark of flooding attacks that overwhelm network resources.

- **Flow Duration** decreases the Web
```

### aud2-138

```
The predicted class is **SSH-Patator**, supported by the following features:

- **Init_Win_bytes_forward** increases the SSH-Patator score. This feature reflects the client's initial TCP window size, which in crafted traffic often has unusual fixed values, indicating a tool-driven pattern typical of SSH-Patator.
- **Init_Win_bytes_backward** increases the SSH-Patator score. This represents the server's initial TCP window size, and a value of -1 suggests the destination did not complete a handshake, a common characteristic of unanswered probes associated with SSH-Patator.
- **URG Flag Count** increases the SSH-Patator score. The presence of non-zero URG flags in both directions is anomalous in modern benign traffic, suggesting deliberate manipulation consistent with SSH-P
```

### aud2-139

```
The model classified this flow as DoS. The most influential factors were: 1. Init_Win_bytes_forward increased the DoS score (magnitude 3.1595); 2. Fwd Packets/s increased the DoS score (magnitude 1.4043); 3. Average Packet Size increased the DoS score (magnitude 1.1826); 4. Bwd Packets/s increased the DoS score (magnitude 1.0940); 5. Flow IAT Min increased the DoS score (magnitude 0.7441).
```

### aud2-140

```
The traffic in question closely aligns with the class profile of SSH-Patator, a brute-force credential guessing attack against SSH services. The evidence begins with the **Bwd Header Length**, which increases the SSH-Patator score by a significant magnitude of 4.8244. This suggests that the traffic involves a high volume of header-only reply streams in the backward direction, likely indicating acknowledgment or reset traffic without actual content—common in automated probing or failed login attempts. Next, the **Total Length of Bwd Packets** also increases the score by 4.3148, pointing to near-zero replies against non-trivial forward traffic, which may reflect unanswered probes or refused services, further supporting the idea of a coordinated scan or brute-force attempt. As the story unfolds
```

### aud2-141

```
SHAP attribution (top-5) for class BENIGN: Init_Win_bytes_backward=+1.8985; Total Backward Packets=+0.9371; Fwd Packet Length Max=+0.6910; Active Min=+0.5358; Average Packet Size=+0.4578
```

### aud2-142

```
The traffic in question was classified as a denial-of-service (DoS) attack due to a pattern of behavior that aligns closely with the characteristics of an HTTP flood attack. The server's initial TCP window size, as indicated by the feature *Init_Win_bytes_backward*, was unusually high, which increased the DoS score. This suggests that the destination system was either under heavy load or was not completing handshakes, a common sign of unanswered probes or refused connections in a DoS scenario. The flow also exhibited very short idle gaps, as reflected by the *Idle Min* feature, which further increased the score—indicating that activity resumed almost immediately after bursts, a behavior typical of sustained or repeated attacks. The *Idle Mean* also contributed to the DoS score, with its relatively
```

### aud2-143

```
The model predicts **Web Attack** based on the following features, each of which contributes to increasing the Web Attack score:

- **Fwd IAT Min** indicates a very short gap between consecutive packets from the source, suggesting packet bursts that are characteristic of attack tools attempting to overwhelm the target.
- **Max Packet Length** being small implies that the flow never carried real data, which is often seen in malicious traffic where the goal is to probe or disrupt rather than transmit meaningful content.
- **Flow IAT Min** is near-zero, indicating back-to-back packet bursts, a sign of flooding behavior typical in Web Attack scenarios.
- **Init_Win_bytes_backward** is -1, meaning the destination never completed a handshake, which is common in unanswered or refused probes, often associated with scanning or
```

### aud2-144

```
Explanation:  
The classification as **BENIGN** is supported by several key features that align with characteristics of non-malicious network behavior.  

- **Init_Win_bytes_backward** increases the BENIGN score, as a positive value indicates the destination completed a TCP handshake, suggesting normal communication rather than an unanswered probe.  
- **Total Backward Packets** increases the BENIGN score, reflecting a balanced exchange of packets between source and destination, which is typical of legitimate traffic rather than one-sided attack patterns.  
- **Fwd Packet Length Max** increases the BENIGN score, as a smaller maximum packet size suggests minimal data transfer, consistent with scan or control-only traffic rather than large-scale data exfiltration.  
- **Active Min** increases the BENIGN score, as a
```

### aud2-145

```
Explanation:  
The classification as **PortScan** is supported by several key features.  

- **Total Length of Fwd Packets** increases the PortScan score. This feature indicates a large volume of data being sent from the source to the destination, which is consistent with active scanning or exfiltration behavior typical in PortScan attacks.  
- **PSH Flag Count** also increases the PortScan score. A high count of PSH flags on small packets suggests scripted, automated exchanges, which aligns with the behavior of scanning tools that send rapid, repetitive requests.  
- **Bwd Packets/s** increases the PortScan score. A low backward packet rate relative to a high forward rate suggests one-sided traffic, where the scanner is sending many packets but receiving few, a hallmark of
```

### aud2-146

```
The traffic in question was flagged as a DDoS attack due to a pattern of behavior that aligns closely with the class profile of distributed denial-of-service: a surge in volumetric traffic originating from multiple sources. The evidence begins with **act_data_pkt_fwd**, which shows that forward packets carried actual payload data, indicating real communication rather than mere probing or handshake-only activity—this increases the DDoS score, suggesting the traffic is not just scanning but actively engaging. Supporting this, **Init_Win_bytes_backward** is also elevated, pointing to a server-side TCP window size that implies a completed handshake, further reinforcing the presence of real, sustained traffic rather than unanswered probes—another boost to the DDoS score. Meanwhile, **Bwd Packet Length Mean** is near-zero, which,
```

### aud2-147

```
Explanation:  
The classification as a **Web Attack** is supported by several key features that align with the characteristics of such attacks.  

- **Fwd IAT Min** is high, indicating near-zero gaps between consecutive packets from the source. This suggests packet bursts, a common behavior in attack tools aiming to overwhelm a system.  
- **Max Packet Length** is large, implying that the flow did not carry real data, which is typical of malicious traffic attempting to bypass normal data transmission patterns.  
- **Flow IAT Min** is low, showing back-to-back packet bursts. This is characteristic of flooding attacks, where packets are sent at an extremely high rate to disrupt normal network operations.  
- **Init_Win_bytes_backward** is negative, indicating that the destination did not complete a
```

### aud2-148

```
The flow was classified as **Bot** due to high **Bwd Packets/s** (29,411.76) and **Flow Packets/s** (58,823.53), indicating a high rate of packets in both directions, which is unusual for normal traffic. Additionally, the **Flow Duration** (34.0) and **Flow IAT Std** (0.0) suggest a very short and consistent interval between packets, typical of automated or bot-driven activity. The **URG Flag Count** (1.0) and **Bwd Header Length** (20.0) also contribute, as they may indicate abnormal packet handling often seen in bot traffic.
```

### aud2-149

```
The classification of this flow as **Bot** is supported by several key features that align with the behavioral patterns of botnet activity:

- **Init_Win_bytes_backward** increases the Bot score. This feature reflects the server's initial TCP window size, and a value of -1 typically indicates that the destination never completed a handshake, which is common in unanswered or refused probes—behavior often seen in botnet scanning or probing activities.

- **Init_Win_bytes_forward** also increases the Bot score. This represents the client's initial TCP window size. Unusual or fixed values here can be indicative of crafted traffic, such as that generated by malicious tools, which often lack proper handshakes, a hallmark of botnet communication.

- **Fwd Header Length** raises the Bot score. A high
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-125` to `aud2-149`, in one fenced block.