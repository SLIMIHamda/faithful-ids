# Annotation task — 17 explanation texts

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


### aud2-000

```
The traffic in question closely aligns with the class profile of FTP-Patator, a brute-force credential guessing attack against an FTP server. The evidence points to a coordinated attempt to exhaustively guess valid login credentials through repeated, systematically varied packet exchanges. The largest contributing factor was the **Max Packet Length**, which increased the FTP-Patator score—suggesting that the flow involved relatively large packets, indicative of actual data transfer rather than minimal header-only traffic, which would be typical of a small or non-functional connection. This implies the attack was not just a probe but an active attempt to interact with the server. The **Bwd Header Length** also increased the score, pointing to a pattern of header-only responses in the backward direction, which is characteristic of automated or machine-generated traffic, such as
```

### aud2-001

```
The flow was classified as **BENIGN** due to its low traffic volume and lack of suspicious flag activity. Lower values for **PSH Flag Count** (1.0) and **Flow Packets/s** (0.59) indicate minimal active communication. Additionally, the **Flow Duration** (111,364,757.0) suggests a long, steady connection rather than a short, potentially malicious burst. These features align with normal, sustained network behavior.
```

### aud2-002

```
Explanation:  
The highest contributing factor was Fwd IAT Min, which significantly increased the Web Attack score by 7.4495. Next, Max Packet Length also increased the score by 4.7825. Flow IAT Min contributed further by increasing the score by 2.0858. Init_Win_bytes_backward added to the score with a magnitude of 1.2049. Finally, Flow Duration increased the score by 0.9704.  
Overall decision: The combination of these factors strongly indicates a Web Attack.
```

### aud2-003

```
Explanation:  
1. The high value of Init_Win_bytes_backward significantly increased the DoS score by 2.9496.  
2. The elevated Idle Min further increased the DoS score by 0.9958.  
3. The increased Idle Mean also contributed to raising the DoS score by 0.9613.  
4. The notable Bwd Packet Length Std added to the DoS score with a magnitude of 0.7817.  
5. The increased FIN Flag Count provided additional support to the DoS score by 0.6414.  

Overall decision: The system classified the activity as DoS due to the cumulative impact of these contributing factors.
```

### aud2-004

```
SHAP attribution (top-5) for class BENIGN: Total Backward Packets=+1.0998; Init_Win_bytes_backward=+0.7365; Fwd Packet Length Max=+0.6988; Active Min=+0.6363; Bwd Packet Length Std=+0.4178
```

### aud2-005

```
The traffic in question was classified as Bot due to a pattern of behavior that aligns closely with the characteristics of a botnet command-and-control channel. The initial sign was the **Init_Win_bytes_backward**, which increased the Bot score, suggesting that the destination system never completed a handshake, a common scenario in unanswered probes or refused connections—typical of automated scanning or probing behavior. This sets the stage for a coordinated, automated interaction. Supporting this, the **Bwd IAT Min** also increased the Bot score, indicating rapid-fire responses from the destination, which could be a rejection storm or a flood of automated replies, further reinforcing the idea of a botnet attempting to overwhelm or test the system. Meanwhile, the **Flow IAT Max** increased the Bot score as well, pointing to
```

### aud2-006

```
The traffic in question is classified as **BENIGN**, reflecting normal, non-malicious behavior, as evidenced by several key features that collectively support this conclusion. The **Init_Win_bytes_forward** value, which indicates the client's initial TCP window size, increases the BENIGN score, suggesting a proper handshake and typical client behavior, as unusual or crafted values would be flagged otherwise. Similarly, the **Bwd Packet Length Min**, representing the smallest packet sent by the destination, also increases the BENIGN score, pointing to minimal-only replies that are characteristic of acknowledgment or rejection traffic without payload, further aligning with benign activity. The **Fwd Packet Length Max**, which captures the largest packet sent by the source, contributes positively to the BENIGN score, implying that no substantial payload was transmitted
```

### aud2-007

```
The traffic in question was classified as a denial-of-service (DoS) attack due to a pattern of behavior that aligns closely with the characteristics of an HTTP flood. The initial TCP window size, as indicated by the **Init_Win_bytes_forward** feature, was unusually high, which increased the DoS score. This suggests a crafted or automated connection, possibly from a tool or a malicious stack, attempting to overwhelm the server with a large initial data payload. As the traffic progressed, the **Bwd Packets/s** rate was notably low, further increasing the DoS score, which points to a one-sided communication where the destination is not reciprocating the traffic at the same rate, a hallmark of an attack. Meanwhile, the **Average Packet Size** was large, also increasing the
```

### aud2-008

```
The model predicts the class **DDoS** based on the following features, each of which contributes to increasing the DDoS score:

1. **Bwd Packet Length Mean**: This feature increases the DDoS score. Near-zero values in backward packet lengths can indicate unanswered scan probes, which are often associated with DDoS activity as they suggest probing behavior without proper responses.

2. **Packet Length Mean**: This feature also increases the DDoS score. Small average packet sizes are indicative of control or probe traffic, which is commonly observed in DDoS attacks as attackers often send small packets to test or initiate traffic.

3. **Init_Win_bytes_backward**: This feature increases the DDoS score. A value of -1 indicates that the destination never completed a handshake, which is
```

### aud2-009

```
Explanation:  
The classification as **BENIGN** is supported by several features that indicate the traffic is likely control, probe, or acknowledgment-only, with minimal payload or no actual data transfer.

- **Init_Win_bytes_forward** increases the BENIGN score. This feature reflects the client's initial TCP window size, which is often fixed and unique to specific tools or stacks. Unusual or fixed values here suggest crafted traffic, which is commonly associated with benign probing or setup traffic rather than malicious activity.

- **Bwd Packet Length Min** increases the BENIGN score. This feature represents the smallest packet sent by the destination, which is typically minimal in acknowledgment or rejection traffic. Such minimal-only replies are characteristic of benign traffic that lacks payload, such as simple responses to probes.

- **Fwd
```

### aud2-010

```
SHAP attribution (top-5) for class DoS: Init_Win_bytes_forward=+1.9851; Bwd Packets/s=+1.2003; Average Packet Size=+1.0177; Fwd Packets/s=+0.5589; Fwd IAT Mean=+0.4325
```

### aud2-011

```
The network flow is classified as **Bot** due to the following features, each contributing to the Bot score in a specific way:

- **Init_Win_bytes_backward** increases the Bot score. This feature reflects the server's initial TCP window size. A value of -1 indicates the destination never completed a handshake, which is typical of unanswered or refused probes—common in botnet activity.
  
- **Init_Win_bytes_forward** increases the Bot score. This feature represents the client's initial TCP window size. Unusual or fixed values here can indicate crafted traffic, such as that generated by bots, which often lack proper handshakes.

- **Fwd Header Length** increases the Bot score. This feature measures the total TCP/IP header bytes in the forward direction. A high header-to-p
```

### aud2-012

```
The traffic in question was classified as a DDoS attack due to a pattern of behavior that aligns closely with the class profile of distributed denial-of-service. The evidence begins with **act_data_pkt_fwd**, which shows that the flow involved forward packets carrying actual payload data, increasing the DDoS score. This suggests that the traffic was not merely a handshake or probe but was actively transmitting content, a hallmark of sustained attack traffic. Supporting this, **Init_Win_bytes_forward** also increased the score, indicating that the client's initial TCP window size was set to an unusual value, a common signature of crafted or automated traffic, often used to mask or amplify attack behavior. As the story unfolds, **Total Backward Packets** further increased the score, revealing an asymmetry in the direction
```

### aud2-013

```
Explanation:  
1. The total length of forward packets significantly increased the PortScan score by 2.2285.  
2. The PSH flag count further increased the PortScan score by 0.8674.  
3. The number of backward packets per second added to the PortScan score with a magnitude of 0.7822.  
4. The flow IAT mean slightly decreased the PortScan score by 0.6310.  
5. The rate of forward packets per second also reduced the PortScan score by 0.4954.  

Overall decision: The network flow was classified as PortScan due to the cumulative effect of these contributing factors.
```

### aud2-014

```
Explanation:  
1. Total Backward Packets increased the BENIGN score by the largest magnitude, indicating a high volume of backward packets associated with benign behavior.  
2. Init_Win_bytes_backward further increased the BENIGN score, suggesting normal flow control patterns typical of benign traffic.  
3. Fwd Packet Length Max contributed positively to the BENIGN score, reflecting consistent and predictable packet sizes.  
4. Active Min added to the BENIGN score, showing stable and continuous network activity.  
5. Bwd Packet Length Std also increased the BENIGN score, indicating consistent backward packet size variations, which are common in benign traffic.  

Overall decision: The network activity is classified as BENIGN based on the cumulative positive contributions from these features.
```

### aud2-015

```
The flow was classified as **Bot** due to several unusual characteristics. A high **PSH Flag Count** (1.0) suggests potential payload manipulation typical of botnet activity. Additionally, the **Fwd Packet Length Std** (97.04) and **Packet Length Std** (76.44) are unusually high, indicating irregular packet sizes often seen in automated, bot-driven traffic. The **Bwd Header Length** (72.0) and **Fwd Header Length** (92.0) are also elevated, which may indicate abnormal TCP header behavior. These features collectively suggest non-human, automated behavior consistent with a bot.
```

### aud2-016

```
Explanation:  
The DDoS score was most significantly increased by high values in `act_data_pkt_fwd`, indicating a strong association with DDoS activity. Next, elevated `Init_Win_bytes_forward` further boosted the DDoS score, suggesting aggressive initial data transmission. A high count of `Total Backward Packets` also contributed to raising the DDoS score, pointing to unusual traffic patterns. Increased `Fwd Packet Length Max` added to the DDoS score, reflecting potential data flooding. Lastly, higher `Fwd IAT Std` slightly increased the DDoS score, showing irregular timing in forward packets.  

Overall decision: The system classified the activity as DDoS due to the cumulative impact of these contributing factors.
```

---

Now output exactly 17 JSONL lines, one per item from `aud2-000` to `aud2-016`, in one fenced block.