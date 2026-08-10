# Extractor audit — annotation chunk 12 of 12

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


### aud2-275

```
The traffic in question was classified as a DDoS attack due to a pattern of behavior that aligns closely with the class profile of distributed denial-of-service. The flow began with a high number of forward packets carrying actual payload data, as indicated by the feature `act_data_pkt_fwd`, which increased the DDoS score. This suggests that the traffic was not merely a handshake or probe but involved real data transmission, a hallmark of coordinated attack activity. Supporting this, the `Init_Win_bytes_forward` value was also elevated, further increasing the score, as it points to a crafted initial TCP window size—often a signature of malicious tools attempting to fingerprint or overwhelm the target. The presence of a significant number of backward packets, as captured by `Total Backward Packets`, also contributed to
```

### aud2-276

```
Explanation:  
1. High values of Init_Win_bytes_forward increased the BENIGN score by 2.2500.  
2. Elevated Bwd Packet Length Min further increased the BENIGN score by 1.0519.  
3. Fwd Packet Length Max contributed to the BENIGN score with an increase of 0.6535.  
4. A lower Idle Min slightly decreased the BENIGN score by 0.3133.  
5. Init_Win_bytes_backward added a smaller increase to the BENIGN score of 0.2692.  

Overall decision: The network traffic was classified as BENIGN based on the cumulative positive contributions from key features outweighing the minor negative influence of Idle Min.
```

### aud2-277

```
The model predicts **Web Attack** based on the following features, each of which contributes to increasing the Web Attack score:

- **Fwd IAT Min** indicates a very short gap between consecutive packets from the source, suggesting packet bursts that are characteristic of attack tools attempting to overwhelm the target.
- **Max Packet Length** being small implies that the flow never carried real data, which is often seen in malicious traffic where the goal is to probe or disrupt rather than transmit meaningful content.
- **Flow IAT Min** is near-zero, indicating back-to-back packet bursts, a sign of flooding behavior typical in Web Attack scenarios.
- **Init_Win_bytes_backward** is -1, meaning the destination never completed a handshake, which is common in unanswered or refused probes, often associated with scanning or
```

### aud2-278

```
SHAP attribution (top-5) for class Web Attack: Fwd IAT Min=+6.3516; Max Packet Length=+4.7387; Flow Duration=-1.4443; Flow IAT Min=+1.3158; Init_Win_bytes_backward=-0.8767
```

### aud2-279

```
Explanation:  
1. A high Bwd Header Length significantly increased the SSH-Patator score by 4.8244.  
2. A large Total Length of Bwd Packets further increased the SSH-Patator score by 4.3185.  
3. A high Fwd Packet Length Std contributed to the SSH-Patator score with an increase of 1.1687.  
4. A high Fwd Packet Length Max added to the SSH-Patator score with an increase of 1.0569.  
5. A high min_seg_size_forward also increased the SSH-Patator score by 0.9677.  

The model predicts the connection is **SSH-Patator** due to the cumulative
```

### aud2-280

```
The flow was classified as **Web Attack** due to high **Bwd Packets/s** (1996.007984), indicating a high rate of backward packets, which is suspicious. Additionally, the **Flow Duration** of 1002.0 seconds suggests a prolonged connection, often seen in malicious activities. The **PSH Flag Count** being 1.0, along with **Bwd Header Length** of 72.0, may indicate unusual packet behavior. These features collectively suggest a potential web-based attack.
```

### aud2-281

```
Explanation:  
The classification as DDoS is supported by several key features that indicate abnormal traffic patterns typical of distributed denial-of-service attacks.  

- **act_data_pkt_fwd** increases the DDoS score because it reflects forward packets carrying actual data, suggesting active transmission of payload, which is characteristic of coordinated attacks.  
- **Init_Win_bytes_backward** increases the DDoS score as it indicates the server's initial TCP window size, with a value of -1 often signaling unanswered or refused probes, a common sign of scanning or probing behavior.  
- **Bwd Packet Length Mean** increases the DDoS score because near-zero values suggest minimal or no data in backward packets, which can indicate unanswered scan probes or refused services.  
- **Fwd Packet Length Max** increases
```

### aud2-282

```
The model classified this flow as DDoS. The most influential factors were: 1. act_data_pkt_fwd increased the DDoS score (magnitude 2.8158); 2. Init_Win_bytes_forward increased the DDoS score (magnitude 1.3858); 3. Total Backward Packets increased the DDoS score (magnitude 1.1480); 4. Fwd Packet Length Max increased the DDoS score (magnitude 0.6765); 5. Fwd IAT Std increased the DDoS score (magnitude 0.5749).
```

### aud2-283

```
The traffic in question was classified as **BENIGN** based on a pattern of features that align closely with normal, non-malicious network behavior. The largest packet observed in the flow, as indicated by the **Max Packet Length**, was relatively large, which suggests that the flow carried real data rather than being a minimal or synthetic transmission—this increased the BENIGN score. Supporting this, the **Packet Length Std** showed a moderate variability, indicating that the packet sizes were not uniform, which is characteristic of legitimate, machine-generated traffic rather than crafted or automated payloads—another boost to the BENIGN score. The **Init_Win_bytes_forward**, which reflects the client's initial TCP window size, was within a typical range, suggesting a proper handshake and not an attempt to mimic or bypass standard
```

### aud2-284

```
The flow was classified as **DoS** due to extremely high **Flow Packets/s** and **Fwd Packets/s** values of 500,000, indicating an unusually high rate of packets being sent in a short time. This suggests a potential flood attack. Additionally, the **Flow Duration** and **Flow IAT Mean/Min/Max** are all 4.0, implying a very short and rapid sequence of packets, which is characteristic of a DoS attack. The **Fwd Header Length** is 64.0, which is normal, but combined with the high packet rate, it reinforces the likelihood of a resource exhaustion attack.
```

### aud2-285

```
The model classified this flow as DoS. The most influential factors were: 1. Init_Win_bytes_backward increased the DoS score (magnitude 2.9496); 2. Idle Min increased the DoS score (magnitude 0.9958); 3. Idle Mean increased the DoS score (magnitude 0.9613); 4. Bwd Packet Length Std increased the DoS score (magnitude 0.7817); 5. FIN Flag Count increased the DoS score (magnitude 0.6414).
```

### aud2-286

```
Explanation:  
1. High Init_Win_bytes_backward significantly increased the Bot score by 4.9280.  
2. High Init_Win_bytes_forward further increased the Bot score by 3.1784.  
3. Increased Fwd Header Length added to the Bot score with a magnitude of 1.9376.  
4. Flow IAT Mean slightly decreased the Bot score by 0.9125.  
5. Elevated Flow Bytes/s contributed to the Bot score with a magnitude of 0.8479.  

Overall decision: The network behavior strongly indicates a Bot based on the cumulative impact of these features.
```

### aud2-287

```
Explanation:  
The highest contributing factor was Fwd IAT Min, which significantly increased the Web Attack score by 7.3025. Next, Max Packet Length also increased the score by 4.7825. Flow IAT Min contributed further by increasing the score by 1.9237. Init_Win_bytes_backward added 0.8456 to the score, as did min_seg_size_forward with 0.8427.  

Overall decision: The system classified the network flow as a Web Attack due to the cumulative increase in the Web Attack score from these contributing factors.
```

### aud2-288

```
The traffic in question closely aligns with the class profile of SSH-Patator, a brute-force credential guessing attack against SSH. The evidence begins with **Init_Win_bytes_forward**, which increases the SSH-Patator score by a significant magnitude of 5.1597. This feature reflects the client's initial TCP window size, and its unusual fixed value suggests a crafted connection, possibly from a tool attempting to fingerprint the target. The **Init_Win_bytes_backward** also increases the score, with a magnitude of 4.3209, indicating the server's initial window size—here, the value of -1 suggests that the destination never completed a handshake, a common sign of unanswered or refused probes, typical in automated scanning attempts. 

The **URG Flag Count
```

### aud2-289

```
The flow was classified as **BENIGN** due to its low activity and minimal packet exchange. The **Bwd Packets/s** value of 21,276.59 indicates a high rate of backward packets, which may suggest normal traffic patterns. Additionally, **Flow Duration** and **Flow IAT Std** being zero suggest a consistent and short-lived connection, typical of benign behavior. The **ACK Flag Count** and **URG Flag Count** being non-zero, while other flag counts like **SYN**, **FIN**, and **RST** are zero, further support a benign classification.
```

### aud2-290

```
The flow was classified as **BENIGN** due to its low activity and minimal data transfer. The **Flow Duration** and **Flow IAT** values (all 47.0) indicate a short, consistent connection, while **Flow Packets/s** and **Fwd Packets/s** are very high, suggesting a rapid but small data exchange. Additionally, **Fwd Packet Length Mean** and **Max Packet Length** are low (2.0), and **Total Length of Fwd Packets** is only 4.0, indicating minimal data volume. These features suggest a normal, low-impact network interaction rather than malicious activity.
```

### aud2-291

```
SHAP attribution (top-5) for class PortScan: Total Length of Fwd Packets=+2.2285; PSH Flag Count=+0.8674; Bwd Packets/s=+0.7822; Flow IAT Mean=-0.6310; Fwd Packets/s=-0.4954
```

### aud2-292

```
The traffic in question was flagged as Bot due to a pattern of features that collectively suggest the presence of automated, coordinated, or malicious network behavior. The initial server-side TCP window size, **Init_Win_bytes_backward**, was unusually high, which increased the Bot score and points to a potential refusal or incomplete handshake, a common sign of probing or scanning activity. This is further supported by the **Init_Win_bytes_forward**, which also increased the Bot score, indicating a client-side configuration that may be non-standard or crafted, often seen in botnet traffic where the client's behavior is controlled or manipulated. The **Fwd Header Length** was also elevated, contributing to the Bot score, and this suggests a high header-to-payload ratio, which is characteristic of control-heavy traffic such as scans or
```

### aud2-293

```
Explanation:  
The classification as **FTP-Patator** is supported by several key features that align with the behavior of this intrusion type.  

- **Max Packet Length** increases the FTP-Patator score. A large maximum packet size suggests the flow carried real data, which is consistent with active FTP attempts where data is transferred.  
- **Bwd Header Length** increases the FTP-Patator score. A high value here indicates header-only traffic in the backward direction, which may represent reset or acknowledgment packets, common in automated FTP probing.  
- **Fwd Packet Length Std** increases the FTP-Patator score. Low variability in forward packet sizes suggests uniform, machine-generated packets, a hallmark of automated tools like FTP-Patator used for brute-force attacks.  
- **Packet
```

### aud2-294

```
Explanation:  
The classification as **SSH-Patator** is supported by several key features that align with the behavior of this intrusion-detection class.  

- **Init_Win_bytes_forward** increases the SSH-Patator score. This feature reflects the client's initial TCP window size, which is often set to unusual values in crafted traffic, such as in SSH-Patator attacks, to fingerprint the tool or bypass standard handshakes.  
- **Init_Win_bytes_backward** also increases the score. This represents the server's initial TCP window size, and a value of -1 typically indicates that the destination did not complete a handshake, a common pattern in unanswered or refused probes associated with automated scanning tools like SSH-Patator.  
- **URG Flag Count** raises the score
```

### aud2-295

```
The flow was classified as **DDoS** due to its unusually long **Flow Duration** and **Flow IAT Std**, indicating irregular timing between packets, which is common in distributed attacks. The **Fwd Packets/s** and **Flow Packets/s** are very low, suggesting a high volume of traffic over an extended period, a hallmark of DDoS. Additionally, the **Fwd Header Length** is significantly higher than typical, which may indicate spoofed or malformed packets often seen in such attacks.
```

### aud2-296

```
Explanation:  
The classification as DDoS is supported by several key features that indicate abnormal traffic patterns consistent with distributed denial-of-service activity.  

- **act_data_pkt_fwd** increases the DDoS score because it reflects forward packets carrying payload data, suggesting active data transfer rather than a handshake-only flow. This is characteristic of sustained attack traffic.  
- **Init_Win_bytes_forward** increases the DDoS score as it indicates a non-standard initial TCP window size, which can be a signature of crafted or malicious traffic, often seen in DDoS attacks.  
- **Total Backward Packets** increases the DDoS score due to the asymmetry between forward and backward traffic, which may suggest one-sided communication typical of attack traffic.  
- **Fwd Packet Length Max
```

### aud2-297

```
SHAP attribution (top-5) for class BENIGN: Max Packet Length=+0.7253; Packet Length Std=+0.5666; Init_Win_bytes_forward=+0.4744; Bwd Packets/s=+0.4197; Fwd Header Length=+0.4112
```

### aud2-298

```
The flow was classified as **Web Attack** due to the presence of **PSH Flag Count = 1.0**, which suggests potential payload manipulation, and **Subflow Fwd Packets = 3.0**, indicating fragmented or unusual packet behavior. Additionally, **Bwd Header Length = 40.0** and **Fwd Header Length = 104.0** suggest abnormal header sizes, which may indicate attempts to bypass security filters. These features collectively point toward suspicious network behavior consistent with a Web Attack.
```

### aud2-299

```
Explanation:  
The classification as **BENIGN** is supported by several key features that align with characteristics of normal, non-malicious network behavior.  

- **Init_Win_bytes_forward** increases the BENIGN score. This feature reflects the client's initial TCP window size, which is often set to specific values by tools or stacks. Unusual or fixed values can indicate crafted traffic, but in this case, the presence of a proper handshake (non-zero value) suggests legitimate communication.  
- **Bwd Packet Length Min** also increases the BENIGN score. This feature represents the smallest packet sent by the destination, which in normal traffic often corresponds to minimal acknowledgment or rejection responses without payload. Such behavior is typical of benign, low-traffic interactions.  
- **Fwd Packet Length
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-275` to `aud2-299`, in one fenced block.