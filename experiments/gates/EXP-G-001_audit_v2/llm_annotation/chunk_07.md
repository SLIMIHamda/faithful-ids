# Extractor audit — annotation chunk 07 of 12

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


### aud2-150

```
Explanation:  
The classification as **SSH-Patator** is supported by several key features that align with the behavior of this intrusion-detection class.  

- **Init_Win_bytes_forward** increases the SSH-Patator score. This feature reflects the client's initial TCP window size, which is often set to unusual values in crafted traffic, such as in SSH-Patator attacks, to fingerprint the tool or bypass standard handshakes.  
- **Init_Win_bytes_backward** also increases the score. This represents the server's initial TCP window size, and a value of -1 typically indicates a failed or refused handshake, which is common in SSH-Patator's probing behavior.  
- **URG Flag Count** raises the score. A non-zero count of URG flags in
```

### aud2-151

```
The flow was classified as **DoS** due to several anomalous features. The **Bwd Header Length** is unusually high (200.0), suggesting potential spoofing or malformed packets. Additionally, **Bwd IAT Max**, **Bwd IAT Std**, and **Bwd IAT Total** are extremely high, indicating irregular and possibly malicious timing patterns. The **Flow Duration** is also exceptionally long (101,556,761.0), which is suspicious for a normal connection. These features collectively suggest an attempt to overwhelm the system, aligning with a **DoS** classification.
```

### aud2-152

```
Explanation:  
The classification as **PortScan** is supported by several key features.  

- **Total Length of Fwd Packets** increases the PortScan score, as very large totals suggest bulk data transfer, which is characteristic of scanning activity.  
- **Init_Win_bytes_forward** increases the PortScan score, as unusual fixed values may indicate crafted traffic, often seen in scanning attempts.  
- **Bwd Packets/s** increases the PortScan score, as a low backward packet rate against a high forward rate suggests one-sided traffic, typical of probing behavior.  
- **PSH Flag Count** increases the PortScan score, as elevated counts on small packets may indicate scripted request-response exchanges, common in scanning.  
- **Flow Bytes/s** increases the PortScan score,
```

### aud2-153

```
The flow was classified as **SSH-Patator** due to high **Bwd Packets/s** (22,222.22) and **Flow Packets/s** (44,444.44), indicating a high rate of packets in both directions, which is characteristic of automated brute-force attacks. The **Flow Duration** of 45.0 seconds and **Flow IAT Mean** of 45.0 suggest a sustained, rapid attack pattern. Additionally, the **Bwd Header Length** of 32.0 and **Fwd Header Length** of 32.0 indicate consistent TCP header sizes, often seen in scripted attacks like SSH-Patator.
```

### aud2-154

```
The traffic in question was flagged as a **Web Attack** due to a combination of behavioral patterns that align closely with known indicators of malicious activity at the web layer. The most significant contributing factor was **Fwd IAT Min**, which showed a near-zero value, indicating a burst of packets from the source—behavior commonly seen in automated attack tools attempting to overwhelm a service. This burstiness is further reinforced by **Flow IAT Min**, also near-zero, suggesting that packets were sent back-to-back with minimal gaps, a hallmark of flood-based attacks. These two features together point to a coordinated effort to saturate the network connection, a tactic often used in denial-of-service or brute-force scenarios. Meanwhile, **Max Packet Length** was unusually small, implying that the flow never carried substantial data,
```

### aud2-155

```
Explanation:  
The classification as a **Web Attack** is supported by several key features that indicate behavior consistent with crafted or malicious traffic.  

- **Fwd IAT Min** increases the Web Attack score. A near-zero value suggests packet bursts, which are often associated with attack tools attempting to overwhelm a system.  
- **Flow IAT Min** also increases the score. Near-zero minima indicate back-to-back packet bursts, a characteristic of flood-based attacks.  
- **Init_Win_bytes_backward** increases the score. A value of -1 implies the destination never completed a handshake, which is typical of unanswered or refused probes, commonly seen in probing or scanning activities.  
- **Init_Win_bytes_forward** increases the score. Unusual or fixed values here may reveal crafted traffic
```

### aud2-156

```
The traffic in question appears to be benign, as evidenced by a pattern of features that align with normal, non-malicious network behavior. The server's initial TCP window size, **Init_Win_bytes_backward**, is notably high, which increases the BENIGN score and suggests a properly established and stable connection, typical of legitimate communication rather than probing or scanning activity. This is further supported by the **Total Backward Packets**, which also increases the BENIGN score—indicating a balanced exchange of packets between the source and destination, rather than one-sided traffic that might signal an attack. The **Fwd Packet Length Max**, another positive contributor to the BENIGN score, shows that the largest packets sent by the source are relatively small, pointing to minimal payload transfer, which is characteristic of control or
```

### aud2-157

```
The traffic in question closely aligns with the class profile of PortScan, as it exhibits characteristics consistent with reconnaissance probing across multiple ports. The high Total Length of Fwd Packets indicates a significant volume of data being sent from the source to the destination, which increases the PortScan score, suggesting potential bulk upload or exfiltration activity, though in this case, it may also reflect a large number of small, one-sided flows typical of probing. This is further supported by the elevated Init_Win_bytes_forward, which increases the PortScan score and may indicate a crafted or non-standard TCP handshake, a common trait in automated scanning tools. The Flow Bytes/s metric also contributes positively to the PortScan score, pointing to a high throughput that could be associated with volumetric traffic, though in this context
```

### aud2-158

```
Explanation:  
The classification as **PortScan** is supported by several key features that align with the behavior of scanning network ports to identify vulnerabilities or establish connections.  

- **Total Length of Fwd Packets** increases the PortScan score, as very large totals suggest bulk data transfer, which is often associated with port scanning activities where probes are followed by data exfiltration.  
- **Init_Win_bytes_forward** increases the PortScan score, indicating a non-standard TCP window size, which is commonly used in crafted traffic to fingerprint systems or evade detection.  
- **PSH Flag Count** increases the PortScan score, as elevated counts on small packets suggest scripted, rapid request-response exchanges typical of probing multiple ports in a scan.  
- **Flow Bytes/s** increases the PortScan
```

### aud2-159

```
The traffic in question was classified as a denial-of-service (DoS) attack due to a pattern of behavior that aligns closely with the characteristics of an HTTP flood. The initial TCP window size, **Init_Win_bytes_forward**, was unusually high, which increased the DoS score and suggests a crafted or automated connection attempt, possibly indicating a tool or stack fingerprint used to initiate a flood. This was followed by a **Fwd Packets/s** rate that was also elevated, further increasing the DoS score and pointing to a high volume of packets being sent from the source, a hallmark of aggressive scanning or flooding. The **Average Packet Size** was large, which increased the DoS score and implies that the traffic was carrying substantial data, consistent with an attempt to overwhelm the target's bandwidth
```

### aud2-160

```
Explanation:  
The classification as **DoS** is supported by several key features.  

- **Init_Win_bytes_forward** increases the DoS score because unusual fixed values in this feature can indicate a crafted traffic pattern, often associated with malicious activity such as denial-of-service attacks.  
- **Fwd Packets/s** increases the DoS score as a high packet rate from the source suggests flooding or aggressive scanning, behaviors typical of DoS attacks.  
- **Average Packet Size** increases the DoS score since large average packet sizes may indicate content transfer, which can be a sign of overwhelming network resources, a common characteristic of DoS attacks.  
- **Bwd Packets/s** increases the DoS score because a low backward packet rate relative to a high forward rate suggests one
```

### aud2-161

```
The predicted class is **SSH-Patator**, supported by the following features:

- **Init_Win_bytes_forward** increases the SSH-Patator score. This feature reflects the client's initial TCP window size, which in crafted traffic often has unusual fixed values, indicating a tool-driven pattern typical of SSH-Patator.
- **Init_Win_bytes_backward** increases the SSH-Patator score. This represents the server's initial TCP window size, and a value of -1 suggests the destination did not complete a handshake, a common behavior in unanswered probes associated with SSH-Patator.
- **URG Flag Count** increases the SSH-Patator score. The presence of non-zero URG flags in both directions is anomalous in modern benign traffic, suggesting deliberate manipulation consistent with SSH-P
```

### aud2-162

```
Explanation:  
The classification as DDoS is supported by several key features. **act_data_pkt_fwd** indicates that forward packets carry payload data, which is characteristic of sustained traffic patterns seen in DDoS attacks. **Init_Win_bytes_forward** suggests a non-standard TCP window size, often used to mask malicious traffic or fingerprint crafted packets. **Total Backward Packets** shows asymmetry in packet flow, a sign of one-sided communication typical in attack scenarios. **Fwd Packet Length Max** being high implies that large packets are being sent, which is common in coordinated DDoS traffic. Lastly, **Fwd IAT Std** being near-zero indicates highly synchronized packet timing, a hallmark of automated, bot-driven traffic used in DDoS attacks.
```

### aud2-163

```
Explanation:  
The classification as **PortScan** is supported by several key features that align with the behavior of scanning activity.  

- **Total Length of Fwd Packets** increases the PortScan score, as very large totals suggest bulk data transfer, which is characteristic of scanning behavior.  
- **Init_Win_bytes_forward** increases the PortScan score, indicating potential crafted traffic through unusual initial window sizes, which are often used in fingerprinting or scanning attempts.  
- **Flow Bytes/s** increases the PortScan score, as high throughput is commonly associated with volumetric traffic, which can be a sign of scanning or probing.  
- **PSH Flag Count** increases the PortScan score, as elevated counts on small packets suggest scripted, rapid exchanges typical of scanning or probing.
```

### aud2-164

```
The model predicts **Web Attack** based on the following features, each of which increases the Web Attack score:

1. **Fwd IAT Min**: This feature indicates the shortest gap in the source's sending. A near-zero value suggests packet bursts, which are characteristic of attack tools attempting to overwhelm a network with rapid, coordinated traffic.

2. **Flow IAT Min**: This represents the shortest gap between consecutive packets. Near-zero minima indicate back-to-back packet bursts, a hallmark of flooding attacks that aim to saturate network bandwidth.

3. **Init_Win_bytes_backward**: This reflects the server's initial TCP window size. A value of -1 means the destination never completed a handshake, which is typical of unanswered or refused probes—common in probing or scanning activities associated with web attacks
```

### aud2-165

```
Explanation:  
1. High values of Init_Win_bytes_forward increased the BENIGN score by 2.6054.  
2. Elevated Bwd Packet Length Min further increased the BENIGN score by 0.9137.  
3. Fwd Packet Length Max contributed to the BENIGN score with an increase of 0.7008.  
4. Init_Win_bytes_backward added a smaller boost to the BENIGN score, 0.2965.  
5. Average Packet Size also increased the BENIGN score by 0.2712.  

The combination of these factors led to the prediction of BENIGN.
```

### aud2-166

```
The model predicts the class **DDoS** based on the following features, each of which contributes to increasing the DDoS score:

1. **act_data_pkt_fwd**: This feature indicates the presence of forward packets carrying payload data. A higher value suggests that data is being actively transmitted in the forward direction, which is characteristic of DDoS attacks where large volumes of data are sent to overwhelm a target.

2. **Init_Win_bytes_backward**: This feature reflects the server's initial TCP window size. A non-zero value indicates that a handshake was completed, which is typical in DDoS scenarios where the attacker establishes connections to initiate traffic.

3. **Bwd Packet Length Mean**: The mean size of backward packets is near-zero in DDoS cases, indicating that the responses from the
```

### aud2-167

```
Explanation:  
The classification as **BENIGN** is supported by several features that align with characteristics of non-malicious network behavior.  

- **Init_Win_bytes_backward** increases the BENIGN score. This feature reflects the server's initial TCP window size, and a value of -1 (indicative of a failed handshake) is typical of unanswered probes, which are often benign in nature.  
- **Total Backward Packets** increases the BENIGN score. A high count of packets sent from destination to source may suggest one-sided communication, which can be normal in scenarios like probes or simple queries.  
- **Fwd Packet Length Max** increases the BENIGN score. A small maximum packet size indicates minimal payload, which is common in scan or control traffic, both of which
```

### aud2-168

```
The model's prediction of **Bot** is supported by the following features, each contributing to the Bot score in the direction indicated:

- **Init_Win_bytes_backward** increases the Bot score. This feature reflects the server's initial TCP window size, with a value of -1 indicating a failed handshake, a common pattern in unanswered probes or refused connections, which aligns with Bot behavior.
- **Bwd IAT Min** increases the Bot score. A near-zero value suggests rapid-fire responses, such as rejection storms, which are indicative of automated or malicious traffic patterns typical of Bot activity.
- **Flow IAT Max** increases the Bot score. A large gap between consecutive packets suggests idle-and-resume behavior, often seen in keep-alive or command-and-control communications, both of which are
```

### aud2-169

```
The model's prediction of **Bot** is supported by the following features:

- **Init_Win_bytes_backward** increases the Bot score. This feature reflects the server's initial TCP window size, and a value of -1 typically indicates a refused or unanswered probe, which is common in botnet traffic.
- **Init_Win_bytes_forward** increases the Bot score. This feature represents the client's initial TCP window size, and unusual or fixed values can indicate crafted traffic, often associated with bot activity.
- **Fwd Header Length** increases the Bot score. A high header-to-payload ratio suggests control-heavy traffic, which is characteristic of scanning or flooding activities typical in botnets.
- **Flow IAT Mean** decreases the Bot score. Very small values indicate flooding, which is a sign
```

### aud2-170

```
The model classified this flow as SSH-Patator. The most influential factors were: 1. Bwd Header Length increased the SSH-Patator score (magnitude 4.8244); 2. Total Length of Bwd Packets increased the SSH-Patator score (magnitude 4.3148); 3. Fwd Packet Length Std increased the SSH-Patator score (magnitude 1.1604); 4. Fwd Packet Length Max increased the SSH-Patator score (magnitude 1.0569); 5. min_seg_size_forward increased the SSH-Patator score (magnitude 0.9651).
```

### aud2-171

```
The model predicts the class **DoS** based on the following features, each of which contributes to increasing the DoS score:

1. **Init_Win_bytes_forward**: This feature indicates the client's initial TCP window size. Unusual or fixed values here may signal a crafted traffic pattern, which is often associated with malicious activity such as denial-of-service attacks. Such values can reveal a lack of proper handshake, pointing toward an attempt to overwhelm the target system.

2. **Fwd Packets/s**: A high rate of packets sent from the source suggests aggressive scanning or flooding behavior, both of which are characteristic of DoS attacks. This feature reflects a potential overload on the network from the client side.

3. **Average Packet Size**: A smaller average packet size may indicate control or probe traffic
```

### aud2-172

```
Explanation:  
The classification as DDoS is supported by several key features. **act_data_pkt_fwd** indicates that forward packets carried actual payload data, suggesting active data transfer rather than simple probing, which aligns with DDoS behavior. **Init_Win_bytes_backward** reflects a server-side TCP window size, and its presence suggests completed handshakes, consistent with coordinated traffic patterns seen in DDoS attacks. **Fwd Packet Length Max** shows large packet sizes, implying real data transmission rather than scan-like or control-only traffic, further pointing to DDoS. **Total Length of Fwd Packets** indicates significant data volume sent from the source, consistent with bulk traffic typical of DDoS. Finally, **Init_Win_bytes_forward** has a negative effect, suggesting
```

### aud2-173

```
Explanation:  
The classification as **SSH-Patator** is supported by several key features that align with the behavior of this intrusion type.  

- **Bwd Header Length** increases the SSH-Patator score. This is because a higher value suggests header-only reply streams, which are characteristic of acknowledgment or reset traffic without content—common in automated probing or scanning activities typical of SSH-Patator.  
- **Total Length of Bwd Packets** increases the SSH-Patator score. This feature highlights near-zero replies against non-trivial forward traffic, indicating unanswered probes or refused services, which are hallmarks of brute-force attempts seen in SSH-Patator attacks.  
- **Fwd Packet Length Std** increases the SSH-Patator score. A near-zero deviation in forward packet
```

### aud2-174

```
The flow was classified as **DDoS** due to its unusually long **Flow Duration** (3,054,004.0) and **Flow IAT Std** (1,525,418.776), indicating irregular and prolonged communication patterns typical of distributed attacks. The **Fwd Header Length** is abnormally high at 100.0, suggesting potential spoofing or malformed packets. Additionally, the **Flow Packets/s** and **Fwd Packets/s** are low (1.637), but the **Total Fwd Packets** is 5, which, combined with the long duration, suggests a sustained, possibly coordinated attack.
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-150` to `aud2-174`, in one fenced block.