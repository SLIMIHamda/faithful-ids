# Extractor audit — annotation chunk 05 of 12

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


### aud2-100

```
The model predicts the DDoS class based on the following features, each of which contributes to increasing the DDoS score:

- **act_data_pkt_fwd**: This feature indicates the presence of forward packets carrying payload data. A non-zero value suggests actual data transmission, which is characteristic of sustained DDoS attacks where traffic is not limited to probes or handshakes.

- **Init_Win_bytes_forward**: This represents the client's initial TCP window size. Unusual or fixed values can signal crafted traffic, such as in DDoS attacks where the traffic is intentionally designed to evade detection or overwhelm systems.

- **Total Backward Packets**: This feature highlights the number of packets sent from the destination to the source. An asymmetry between forward and backward packets can indicate one-sided traffic patterns
```

### aud2-101

```
Explanation:  
The classification as **DoS** is supported by several key features that align with the characteristics of distributed denial-of-service attacks.  

- **Init_Win_bytes_backward** increases the DoS score, as this feature reflects the server's initial TCP window size. A value of -1, typical in DoS scenarios, indicates that the destination never completed a handshake, suggesting unanswered or refused probes—common in volumetric attacks.  
- **Idle Mean** increases the DoS score, as it represents the mean idle gap between activity bursts. Long, regular idles are characteristic of periodic beaconing and keep-alive command channels, which are often used to maintain connections in sustained attack traffic.  
- **Init_Win_bytes_forward** increases the DoS score, as it reflects the
```

### aud2-102

```
The model predicts the class **DDoS** based on the following features, each of which contributes to increasing the DDoS score:

1. **act_data_pkt_fwd**: This feature indicates the presence of forward packets carrying payload data. A non-zero value suggests actual data transmission, which is characteristic of DDoS attacks where large volumes of data are sent to overwhelm a target.

2. **Init_Win_bytes_forward**: This represents the client's initial TCP window size. Unusual or fixed values can indicate crafted traffic, such as in DDoS attacks, where the initial handshake is manipulated to mimic malicious behavior.

3. **Total Backward Packets**: This feature counts the number of packets sent from the destination to the source. A high value may indicate asymmetry in traffic flow, which
```

### aud2-103

```
The traffic in question closely aligns with the class profile of FTP-Patator, a brute-force credential guessing attack against an FTP server. The evidence points to a coordinated attempt to exhaustively guess valid login credentials through repeated, systematically varied packet exchanges. The largest contributing factor was the **Max Packet Length**, which increased the FTP-Patator score—suggesting that the flow involved relatively large packets, indicative of actual data transfer rather than minimal header-only traffic, which would be typical of a small or non-functional connection. This implies the attack was not just a probe but an active attempt to interact with the server. The **Bwd Header Length** also increased the score, pointing to a pattern of header-only responses in the backward direction, which is characteristic of automated or machine-generated traffic, such as
```

### aud2-104

```
Explanation:  
1. A high Bwd Packet Length Mean significantly increased the DDoS score by 1.5123.  
2. A high Packet Length Mean further increased the DDoS score by 1.4887.  
3. A high Init_Win_bytes_backward contributed to the DDoS score with a magnitude of 1.4557.  
4. A high Total Length of Bwd Packets added to the DDoS score by 1.4227.  
5. A high Fwd Packet Length Max slightly increased the DDoS score by 0.8490.  

The model predicts DDoS based on the cumulative impact of these contributing factors.
```

### aud2-105

```
Explanation:  
1. High Init_Win_bytes_forward significantly increased the Web Attack score by 4.5109.  
2. High Init_Win_bytes_backward further increased the Web Attack score by 4.0522.  
3. A high URG Flag Count contributed to the Web Attack score with a magnitude of 0.9659.  
4. Larger min_seg_size_forward added to the Web Attack score with a magnitude of 0.6676.  
5. Extended Flow Duration increased the Web Attack score by 0.5196.  

The system classified the activity as a Web Attack due to the cumulative impact of these contributing factors.
```

### aud2-106

```
The flow was classified as **FTP-Patator** due to several key features indicating automated, repetitive brute-force attempts. A **high PSH Flag Count (1.0)** suggests payload negotiation, common in FTP. **High Bwd Header Length (488.0)** and **high Fwd Header Length (296.0)** indicate large headers, often used to bypass rate limits. Additionally, **low Average Packet Size (12.33)** and **low Avg Fwd Segment Size (12.0)** suggest small, frequent data transfers typical of automated login attempts. These features align with the behavior of FTP-Patator, a tool used for credential stuffing.
```

### aud2-107

```
The flow was classified as **DDoS** due to high **Flow Packets/s** (162.74) and **Bwd Packets/s** (108.49), indicating a high rate of packets in both directions, which is common in DDoS attacks. Additionally, the **Down/Up Ratio** of 2.0 suggests more bytes sent from the target to the source than vice versa, a pattern often seen in DDoS traffic. The **Bwd Header Length** of 132.0 and **Bwd Packet Length Std** of 2538.92 also indicate irregular and potentially malicious traffic patterns.
```

### aud2-108

```
The model classified this flow as FTP-Patator. The most influential factors were: 1. Max Packet Length increased the FTP-Patator score (magnitude 6.3059); 2. Bwd Header Length increased the FTP-Patator score (magnitude 5.8738); 3. Fwd Packet Length Std increased the FTP-Patator score (magnitude 3.4468); 4. Packet Length Std increased the FTP-Patator score (magnitude 1.0859); 5. Init_Win_bytes_backward increased the FTP-Patator score (magnitude 0.7394).
```

### aud2-109

```
Explanation:  
The classification as DDoS is supported by several key features. **act_data_pkt_fwd** indicates that forward packets carry payload data, which is consistent with sustained traffic typical of DDoS attacks. **Init_Win_bytes_forward** suggests a non-standard TCP window size, a sign of crafted or malicious traffic. **Total Backward Packets** shows asymmetry in packet flow, pointing to one-sided communication often seen in attack scenarios. **Flow IAT Min** reflects near-zero gaps between packets, characteristic of bursty flood traffic. Lastly, **Fwd Packet Length Max** being small implies minimal payload, consistent with scan or control traffic often associated with DDoS. Each of these features aligns with the behavior patterns of a DDoS attack.
```

### aud2-110

```
The model predicts the class **DDoS** based on the following features, each of which contributes to increasing the DDoS score:

1. **Init_Win_bytes_backward**: This feature increases the DDoS score. A value of -1 indicates the destination never completed a handshake, which is typical of unanswered or refused probes—common in DDoS attacks where the target is scanned or probed without establishing a full connection.

2. **act_data_pkt_fwd**: This feature increases the DDoS score. A non-zero value indicates forward packets carrying payload data, suggesting active data transfer. In the context of DDoS, this may reflect coordinated traffic attempting to overwhelm the target with data.

3. **Bwd Packet Length Mean**: This feature increases the DDoS score. A
```

### aud2-111

```
The predicted class is **BENIGN**, supported by the following features:

- **Init_Win_bytes_forward** increases the BENIGN score. This feature reflects the client's initial TCP window size, which is often a fixed value in crafted traffic. A proper handshake is typically indicated by a valid value, and its presence suggests normal, non-malicious communication.
  
- **Bwd Packet Length Min** increases the BENIGN score. This feature represents the smallest packet sent by the destination, which in normal traffic often indicates minimal-only replies—such as acknowledgments or rejections without payload. This behavior is typical of benign, low-impact traffic.

- **Fwd Packet Length Max** increases the BENIGN score. This feature captures the largest packet sent by the source. A small maximum packet
```

### aud2-112

```
Explanation:  
The classification as **DoS** is supported by several key features that align with the characteristics of distributed denial-of-service attacks.  

- **Init_Win_bytes_forward** increases the DoS score because an unusual or fixed initial TCP window size can indicate crafted traffic, often used in fingerprinting attacks to mimic legitimate connections while hiding malicious activity.  
- **Average Packet Size** increases the DoS score as a large average suggests content transfer, which is common in flooding attacks where the goal is to overwhelm the target with high-volume traffic.  
- **Bwd Packets/s** increases the DoS score because a low backward packet rate relative to a high forward rate indicates one-sided traffic, a hallmark of attacks where the attacker sends data but does not receive meaningful responses.  
- **
```

### aud2-113

```
Explanation:  
The classification as **DoS** is supported by several key features.  

- **Init_Win_bytes_forward** increases the DoS score because unusual fixed values in this feature may indicate a crafted traffic pattern, often associated with malicious fingerprinting or tool-based attacks.  
- **Bwd Packets/s** increases the DoS score as a low backward packet rate against a high forward rate suggests one-sided traffic, which is characteristic of attack behavior.  
- **Average Packet Size** increases the DoS score since a larger average packet size may indicate content transfer, which can be a sign of a distributed denial-of-service attack.  
- **Fwd Packets/s** increases the DoS score because a high forward packet rate suggests flooding or aggressive scanning from the client side, consistent
```

### aud2-114

```
The flow was classified as **BENIGN** due to its low traffic volume and lack of suspicious flags. The **Flow Duration** and **Flow IAT Total** indicate a long, steady connection, which is typical of normal, sustained communication. Additionally, **PSH Flag Count = 1.0** suggests minimal urgent data transmission, and **ACK Flag Count = 0.0** indicates no retransmissions, both of which are common in benign traffic. The **Subflow Fwd Packets = 9.0** and **Subflow Bwd Packets = 6.0** show a balanced bidirectional flow, further supporting the benign classification.
```

### aud2-115

```
The traffic in question exhibits characteristics strongly aligned with a DDoS attack, as evidenced by a pattern of features that collectively suggest a coordinated effort to overwhelm a target system with volumetric traffic. The presence of a high magnitude in **act_data_pkt_fwd**, which measures forward packets carrying at least one payload byte, indicates that the flow is not merely a handshake or probe but involves actual data transmission, a key sign of sustained, potentially malicious activity. This feature increases the DDoS score, reinforcing the likelihood of an attack. Complementing this is **Init_Win_bytes_backward**, which reflects the server's initial TCP window size; its elevated value suggests a more substantial data exchange, further increasing the DDoS score and pointing to a flow that is not limited to simple probing. Meanwhile, **
```

### aud2-116

```
The model predicts the class **DoS** based on the following features:

1. **Init_Win_bytes_forward** increases the DoS score. This feature reflects the client's initial TCP window size, which can reveal crafted traffic through unusual, fixed values. Such values may indicate a lack of proper handshake, a common characteristic in DoS attacks where traffic is often generated by tools or malicious scripts.

2. **Bwd Packets/s** increases the DoS score. This feature measures the packet rate from the destination. A low backward rate against a high forward rate suggests one-sided traffic, which is typical in DoS attacks where the destination receives a high volume of traffic from a single source, while the reverse traffic is minimal.

3. **Average Packet Size** increases the DoS score.
```

### aud2-117

```
The flow was classified as **SSH-Patator** due to high **Bwd Packets/s** (12500.0) and **Flow Packets/s** (25000.0), indicating a high rate of packets in the backward direction, which is characteristic of automated brute-force attacks. Additionally, **Subflow Bwd Packets** (1.0) and **Subflow Fwd Packets** (1.0) suggest a small but significant number of packets in both directions, consistent with SSH enumeration attempts. The **Bwd Header Length** (32.0) and **Fwd Header Length** (32.0) also align with typical SSH traffic patterns.
```

### aud2-118

```
The traffic in question was flagged as a **Web Attack** due to a pattern of behavior that aligns closely with known indicators of malicious activity at the web layer. The shortest gap between consecutive packets, **Flow IAT Min**, was extremely low, suggesting a flood of back-to-back packets, a hallmark of network-based attacks. This low value increased the Web Attack score, reinforcing the suspicion of a coordinated assault. Similarly, **Fwd IAT Min** was also very low, indicating that the source was sending packets in rapid bursts—another sign of automated or malicious tools attempting to overwhelm the target. These short intervals between packets are often seen in attacks like brute force or denial-of-service attempts, both of which fall under the broader category of web-layer threats. The **Max Packet Length** was
```

### aud2-119

```
Explanation:  
The highest contributing factor was Max Packet Length, which increased the FTP-Patator score by 6.3059. Next, Bwd Header Length also increased the score by 5.8738. Fwd Packet Length Std contributed by increasing the score by 3.4219. Packet Length Std further increased the score by 1.0442. Finally, Init_Win_bytes_backward added 0.7394 to the FTP-Patator score.  

Overall decision: The network traffic was classified as FTP-Patator due to the cumulative effect of these contributing factors increasing the predicted score.
```

### aud2-120

```
The prediction of **FTP-Patator** is supported by the following features, each contributing to the score in a specific way:

- **Max Packet Length** increases the FTP-Patator score. This suggests that the flow involves relatively large packets, which is characteristic of FTP traffic where data is transferred in larger chunks, as opposed to small, fragmented packets typical of benign traffic.

- **Bwd Header Length** increases the FTP-Patator score. A high value here indicates that the backward direction of the flow consists largely of TCP/IP headers, which may suggest header-only replies—common in FTP responses or reset traffic, often associated with automated probing or scanning behavior.

- **Fwd Packet Length Std** increases the FTP-Patator score. A low variability in forward packet sizes indicates uniform packet
```

### aud2-121

```
The prediction of **FTP-Patator** is supported by the following features, each of which contributes to increasing the FTP-Patator score:

1. **Max Packet Length** increases the score. A high value indicates that the flow carried real data, which is characteristic of active FTP attempts where larger packets are transmitted during brute-force or credential guessing.

2. **Bwd Header Length** increases the score. A larger value suggests that the backward direction of the flow consists of header-only packets, which is typical of acknowledgment or reset traffic seen in FTP brute-force attempts, where the server responds with minimal content.

3. **Fwd Packet Length Std** increases the score. A high variability in forward packet sizes indicates non-uniform traffic, which is inconsistent with machine-generated uniform packets often seen in automated
```

### aud2-122

```
The flow was classified as **DoS** due to an extremely high **Flow Packets/s** (9132.42) and **Fwd Packets/s** (9132.42), indicating a high rate of packets being sent forward, which is suspicious for a denial-of-service attack. Additionally, the **Flow Duration** and **Flow IAT Mean/Max/Min** are all 219.0, suggesting a single, prolonged connection with no inter-arrival time variation, which is unusual. The **Fwd Header Length** is 64.0, which may indicate a large header size, potentially used to overwhelm the target. These features collectively suggest an abnormal traffic pattern consistent with a DoS attack.
```

### aud2-123

```
SHAP attribution (top-5) for class BENIGN: Init_Win_bytes_backward=+1.8986; Total Backward Packets=+1.0733; Fwd Packet Length Max=+0.6455; Active Min=+0.6024; Fwd IAT Std=+0.4211
```

### aud2-124

```
The traffic in question was classified as a denial-of-service (DoS) attack due to a pattern of behavior that aligns closely with the characteristics of an HTTP flood. The initial TCP window size, **Init_Win_bytes_forward**, was unusually high, which increased the DoS score and suggests a crafted or automated connection attempt, possibly indicating a tool or stack fingerprint used to initiate a flood. This was followed by a **Fwd Packets/s** rate that was also elevated, further increasing the DoS score and pointing to a high volume of packets being sent from the source, a hallmark of aggressive scanning or flooding. The **Average Packet Size** was large, which increased the DoS score and implies that the traffic was carrying substantial data, consistent with an attempt to overwhelm the target's bandwidth
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-100` to `aud2-124`, in one fenced block.