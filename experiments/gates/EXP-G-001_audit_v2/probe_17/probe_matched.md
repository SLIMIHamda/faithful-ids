# Annotation task — 17 explanation texts

You are annotating explanation texts about network-traffic classification. Read
each text and report **what the text itself claims**. No other context is needed
and none is relevant.

## Task

Each item gives a text and a list of features. For **every feature in the list**,
say what the text claims about that feature's effect on the score for the class
the text is arguing for:

- `"+"` — the text says this feature raises / pushes up that score
- `"-"` — the text says it lowers / pushes down that score
- `"unclear"` — the text names the feature but commits to no direction
- `"absent"` — the text does not discuss this feature at all

Some listed features are **not** in the text. `absent` is the correct answer for
those and is expected to occur.

Also set `"hedged": true` when the text gives a direction but softens it
("may slightly reduce", "possibly raises").

## Rules

1. Report **only what the prose says**. Do not judge whether the text is correct
   about the traffic — that is a different question and is not being asked.
2. A text may paraphrase a feature ("maximum forward packet length" for
   `Fwd Packet Length Max`). A paraphrase still counts as discussing it.
3. Answer for **every** listed feature of every item. Do not add features.
4. Output one JSON object per line (JSONL), one line per item, in the order
   given, inside a single fenced code block. No commentary before or after.

## Output format

```jsonl
{"item_id": "aud2-000", "claims": [{"feature": "Flow Duration", "dir": "+", "hedged": false}]}
```

---

## Items


### aud2-000

```
The traffic in question closely aligns with the class profile of FTP-Patator, a brute-force credential guessing attack against an FTP server. The evidence points to a coordinated attempt to exhaustively guess valid login credentials through repeated, systematically varied packet exchanges. The largest contributing factor was the **Max Packet Length**, which increased the FTP-Patator score—suggesting that the flow involved relatively large packets, indicative of actual data transfer rather than minimal header-only traffic, which would be typical of a small or non-functional connection. This implies the attack was not just a probe but an active attempt to interact with the server. The **Bwd Header Length** also increased the score, pointing to a pattern of header-only responses in the backward direction, which is characteristic of automated or machine-generated traffic, such as
```

Features to judge:
- `Max Packet Length`
- `Bwd Header Length`
- `Total Backward Packets`
- `Fwd IAT Min`

### aud2-001

```
The flow was classified as **BENIGN** due to its low traffic volume and lack of suspicious flag activity. Lower values for **PSH Flag Count** (1.0) and **Flow Packets/s** (0.59) indicate minimal active communication. Additionally, the **Flow Duration** (111,364,757.0) suggests a long, steady connection rather than a short, potentially malicious burst. These features align with normal, sustained network behavior.
```

Features to judge:
- `Flow Duration`
- `Packet Length Std`
- `Flow Packets/s`
- `Down/Up Ratio`
- `PSH Flag Count`

### aud2-002

```
Explanation:  
The highest contributing factor was Fwd IAT Min, which significantly increased the Web Attack score by 7.4495. Next, Max Packet Length also increased the score by 4.7825. Flow IAT Min contributed further by increasing the score by 2.0858. Init_Win_bytes_backward added to the score with a magnitude of 1.2049. Finally, Flow Duration increased the score by 0.9704.  
Overall decision: The combination of these factors strongly indicates a Web Attack.
```

Features to judge:
- `Fwd Packet Length Std`
- `Fwd IAT Min`
- `Flow Duration`
- `Max Packet Length`
- `Init_Win_bytes_backward`
- `Flow IAT Min`
- `Total Backward Packets`

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

Features to judge:
- `Idle Mean`
- `Bwd Packet Length Std`
- `Packet Length Std`
- `Max Packet Length`
- `FIN Flag Count`
- `Subflow Fwd Packets`
- `Init_Win_bytes_backward`
- `Idle Min`

### aud2-004

```
SHAP attribution (top-5) for class BENIGN: Total Backward Packets=+1.0998; Init_Win_bytes_backward=+0.7365; Fwd Packet Length Max=+0.6988; Active Min=+0.6363; Bwd Packet Length Std=+0.4178
```

Features to judge:
- `Fwd Avg Bytes/Bulk`
- `Total Backward Packets`
- `Init_Win_bytes_backward`
- `Bwd IAT Min`
- `Packet Length Std`
- `Fwd Packet Length Max`
- `Bwd Packet Length Std`
- `Active Min`

### aud2-005

```
The traffic in question was classified as Bot due to a pattern of behavior that aligns closely with the characteristics of a botnet command-and-control channel. The initial sign was the **Init_Win_bytes_backward**, which increased the Bot score, suggesting that the destination system never completed a handshake, a common scenario in unanswered probes or refused connections—typical of automated scanning or probing behavior. This sets the stage for a coordinated, automated interaction. Supporting this, the **Bwd IAT Min** also increased the Bot score, indicating rapid-fire responses from the destination, which could be a rejection storm or a flood of automated replies, further reinforcing the idea of a botnet attempting to overwhelm or test the system. Meanwhile, the **Flow IAT Max** increased the Bot score as well, pointing to
```

Features to judge:
- `Bwd Packet Length Min`
- `Flow IAT Max`
- `Bwd IAT Min`
- `Bwd IAT Max`
- `Init_Win_bytes_backward`

### aud2-006

```
The traffic in question is classified as **BENIGN**, reflecting normal, non-malicious behavior, as evidenced by several key features that collectively support this conclusion. The **Init_Win_bytes_forward** value, which indicates the client's initial TCP window size, increases the BENIGN score, suggesting a proper handshake and typical client behavior, as unusual or crafted values would be flagged otherwise. Similarly, the **Bwd Packet Length Min**, representing the smallest packet sent by the destination, also increases the BENIGN score, pointing to minimal-only replies that are characteristic of acknowledgment or rejection traffic without payload, further aligning with benign activity. The **Fwd Packet Length Max**, which captures the largest packet sent by the source, contributes positively to the BENIGN score, implying that no substantial payload was transmitted
```

Features to judge:
- `Fwd Packet Length Max`
- `Bwd Packet Length Min`
- `Subflow Bwd Packets`
- `Fwd Header Length`
- `Init_Win_bytes_forward`

### aud2-007

```
The traffic in question was classified as a denial-of-service (DoS) attack due to a pattern of behavior that aligns closely with the characteristics of an HTTP flood. The initial TCP window size, as indicated by the **Init_Win_bytes_forward** feature, was unusually high, which increased the DoS score. This suggests a crafted or automated connection, possibly from a tool or a malicious stack, attempting to overwhelm the server with a large initial data payload. As the traffic progressed, the **Bwd Packets/s** rate was notably low, further increasing the DoS score, which points to a one-sided communication where the destination is not reciprocating the traffic at the same rate, a hallmark of an attack. Meanwhile, the **Average Packet Size** was large, also increasing the
```

Features to judge:
- `Average Packet Size`
- `Bwd Packets/s`
- `Init_Win_bytes_forward`
- `Total Length of Bwd Packets`
- `Fwd PSH Flags`

### aud2-008

```
The model predicts the class **DDoS** based on the following features, each of which contributes to increasing the DDoS score:

1. **Bwd Packet Length Mean**: This feature increases the DDoS score. Near-zero values in backward packet lengths can indicate unanswered scan probes, which are often associated with DDoS activity as they suggest probing behavior without proper responses.

2. **Packet Length Mean**: This feature also increases the DDoS score. Small average packet sizes are indicative of control or probe traffic, which is commonly observed in DDoS attacks as attackers often send small packets to test or initiate traffic.

3. **Init_Win_bytes_backward**: This feature increases the DDoS score. A value of -1 indicates that the destination never completed a handshake, which is
```

Features to judge:
- `Init_Win_bytes_backward`
- `Bwd Packet Length Mean`
- `Fwd Packets/s`
- `Average Packet Size`
- `Packet Length Mean`
- `Idle Max`

### aud2-009

```
Explanation:  
The classification as **BENIGN** is supported by several features that indicate the traffic is likely control, probe, or acknowledgment-only, with minimal payload or no actual data transfer.

- **Init_Win_bytes_forward** increases the BENIGN score. This feature reflects the client's initial TCP window size, which is often fixed and unique to specific tools or stacks. Unusual or fixed values here suggest crafted traffic, which is commonly associated with benign probing or setup traffic rather than malicious activity.

- **Bwd Packet Length Min** increases the BENIGN score. This feature represents the smallest packet sent by the destination, which is typically minimal in acknowledgment or rejection traffic. Such minimal-only replies are characteristic of benign traffic that lacks payload, such as simple responses to probes.

- **Fwd
```

Features to judge:
- `Flow IAT Std`
- `Bwd Packet Length Min`
- `Init_Win_bytes_forward`
- `Total Length of Fwd Packets`

### aud2-010

```
SHAP attribution (top-5) for class DoS: Init_Win_bytes_forward=+1.9851; Bwd Packets/s=+1.2003; Average Packet Size=+1.0177; Fwd Packets/s=+0.5589; Fwd IAT Mean=+0.4325
```

Features to judge:
- `Bwd IAT Max`
- `Init_Win_bytes_forward`
- `Fwd Packets/s`
- `Active Max`
- `Fwd IAT Mean`
- `Average Packet Size`
- `Bwd Packets/s`

### aud2-011

```
The network flow is classified as **Bot** due to the following features, each contributing to the Bot score in a specific way:

- **Init_Win_bytes_backward** increases the Bot score. This feature reflects the server's initial TCP window size. A value of -1 indicates the destination never completed a handshake, which is typical of unanswered or refused probes—common in botnet activity.
  
- **Init_Win_bytes_forward** increases the Bot score. This feature represents the client's initial TCP window size. Unusual or fixed values here can indicate crafted traffic, such as that generated by bots, which often lack proper handshakes.

- **Fwd Header Length** increases the Bot score. This feature measures the total TCP/IP header bytes in the forward direction. A high header-to-p
```

Features to judge:
- `Fwd Header Length`
- `Flow Bytes/s`
- `Init_Win_bytes_forward`
- `Init_Win_bytes_backward`
- `Idle Mean`

### aud2-012

```
The traffic in question was classified as a DDoS attack due to a pattern of behavior that aligns closely with the class profile of distributed denial-of-service. The evidence begins with **act_data_pkt_fwd**, which shows that the flow involved forward packets carrying actual payload data, increasing the DDoS score. This suggests that the traffic was not merely a handshake or probe but was actively transmitting content, a hallmark of sustained attack traffic. Supporting this, **Init_Win_bytes_forward** also increased the score, indicating that the client's initial TCP window size was set to an unusual value, a common signature of crafted or automated traffic, often used to mask or amplify attack behavior. As the story unfolds, **Total Backward Packets** further increased the score, revealing an asymmetry in the direction
```

Features to judge:
- `Total Backward Packets`
- `CWE Flag Count`
- `Avg Fwd Segment Size`
- `Init_Win_bytes_forward`
- `act_data_pkt_fwd`

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

Features to judge:
- `Fwd Packets/s`
- `Flow IAT Mean`
- `PSH Flag Count`
- `Bwd IAT Max`
- `Total Backward Packets`
- `Total Length of Fwd Packets`
- `Bwd Packets/s`
- `Flow IAT Max`

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

Features to judge:
- `Init_Win_bytes_backward`
- `Active Min`
- `Max Packet Length`
- `Total Backward Packets`
- `Fwd Packet Length Max`
- `Packet Length Std`
- `Bwd Packet Length Std`
- `Bwd Packets/s`

### aud2-015

```
The flow was classified as **Bot** due to several unusual characteristics. A high **PSH Flag Count** (1.0) suggests potential payload manipulation typical of botnet activity. Additionally, the **Fwd Packet Length Std** (97.04) and **Packet Length Std** (76.44) are unusually high, indicating irregular packet sizes often seen in automated, bot-driven traffic. The **Bwd Header Length** (72.0) and **Fwd Header Length** (92.0) are also elevated, which may indicate abnormal TCP header behavior. These features collectively suggest non-human, automated behavior consistent with a bot.
```

Features to judge:
- `PSH Flag Count`
- `Fwd IAT Max`
- `Bwd IAT Std`
- `Fwd Header Length`
- `Fwd Packet Length Std`
- `Bwd Header Length`
- `Packet Length Std`

### aud2-016

```
Explanation:  
The DDoS score was most significantly increased by high values in `act_data_pkt_fwd`, indicating a strong association with DDoS activity. Next, elevated `Init_Win_bytes_forward` further boosted the DDoS score, suggesting aggressive initial data transmission. A high count of `Total Backward Packets` also contributed to raising the DDoS score, pointing to unusual traffic patterns. Increased `Fwd Packet Length Max` added to the DDoS score, reflecting potential data flooding. Lastly, higher `Fwd IAT Std` slightly increased the DDoS score, showing irregular timing in forward packets.  

Overall decision: The system classified the activity as DDoS due to the cumulative impact of these contributing factors.
```

Features to judge:
- `act_data_pkt_fwd`
- `Total Backward Packets`
- `Fwd Avg Bulk Rate`
- `Bwd Header Length`
- `Init_Win_bytes_forward`
- `Fwd Packet Length Max`
- `Fwd IAT Std`

---

Now output exactly 17 JSONL lines, one per item from `aud2-000` to `aud2-016`, each answering for every listed feature of that item (104 judgments in total), in one fenced block.