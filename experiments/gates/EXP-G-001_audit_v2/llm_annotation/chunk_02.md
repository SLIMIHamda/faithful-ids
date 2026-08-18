# Extractor audit — annotation chunk 02 of 12

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


### aud2-025

```
The predicted class is **BENIGN**, supported by the following features:

- **Init_Win_bytes_forward** increases the BENIGN score. This feature reflects the client's initial TCP window size, which is often a fixed value in crafted or legitimate traffic. Unusual or fixed values can indicate a lack of handshake anomalies, aligning with benign behavior.

- **Bwd Packet Length Min** increases the BENIGN score. This feature represents the smallest packet sent by the destination, which in benign traffic often indicates minimal-only replies—such as acknowledgments or rejections without payload—common in non-malicious communication.

- **Fwd Packet Length Max** increases the BENIGN score. This feature captures the largest packet sent by the source. A small maximum packet size suggests no real payload was carried
```

### aud2-026

```
The traffic in question exhibits characteristics that align closely with the profile of benign activity. The initial TCP window size on the client side, **Init_Win_bytes_forward**, is notably high, which increases the BENIGN score and suggests a properly established and tool-agnostic connection, as this value is typically consistent with normal client behavior rather than crafted or malicious traffic. Complementing this, the server's initial TCP window size, **Init_Win_bytes_backward**, also contributes positively to the BENIGN score, indicating a completed handshake and no signs of refused or unanswered probes, further reinforcing the legitimacy of the connection. The **Average Packet Size** is moderate, increasing the BENIGN score and pointing toward typical data transfer rather than control or probe traffic, which often features smaller packet sizes. This is further supported by
```

### aud2-027

```
Explanation:  
The highest contributing factor was Fwd IAT Min, which significantly increased the Web Attack score by 5.9870. Next, Max Packet Length also increased the score by 4.7825. Flow IAT Min further raised the score by 1.5609. Flow Duration slightly decreased the score by 1.4422. Finally, min_seg_size_forward added a smaller increase of 0.6789.  
Overall decision: The network traffic was classified as a Web Attack due to the cumulative effect of these contributing factors.
```

### aud2-028

```
Explanation:  
The classification as **SSH-Patator** is supported by several key features that align with the behavior of this intrusion-detection class.  

- **Init_Win_bytes_forward** increases the SSH-Patator score. This feature reflects the client's initial TCP window size, which is often set to unusual values in crafted traffic, such as in SSH-Patator attacks, to fingerprint the tool or bypass standard handshakes.  
- **Init_Win_bytes_backward** also increases the score. This represents the server's initial TCP window size, and a value of -1 typically indicates that the destination did not complete a handshake, a common pattern in unanswered or refused probes associated with automated scanning tools like SSH-Patator.  
- **URG Flag Count** raises the score
```

### aud2-029

```
Explanation:  
The Total Length of Fwd Packets significantly increased the PortScan score by 2.1036, indicating a strong contribution to the detection. The Bwd Packets/s further increased the score by 1.2072, amplifying the suspicion of a scan. Init_Win_bytes_forward added 1.1976 to the score, reinforcing the likelihood of a scan. The PSH Flag Count contributed 1.0046, adding to the evidence. Flow Duration increased the score by 0.7669, solidifying the classification.  

Overall decision: The network flow was classified as a PortScan due to the cumulative impact of these contributing factors.
```

### aud2-030

```
The flow was classified as **PortScan** due to high **Bwd Packets/s** (41,666.67) and **Flow Packets/s** (83,333.33), indicating a high rate of packets sent in a short time, which is typical of scanning behavior. Additionally, **PSH Flag Count = 1.0** suggests push flags were used, often seen in scanning activities. The **Flow Duration = 24.0** and **Flow IAT Std = 0.0** indicate a consistent, rapid sequence of packets, further supporting the PortScan classification.
```

### aud2-031

```
Explanation:  
The DDoS score was most significantly increased by high values in `act_data_pkt_fwd`, indicating a strong association with DDoS activity. Next, elevated `Init_Win_bytes_forward` further boosted the DDoS score, suggesting aggressive initial data transmission. A high count of `Total Backward Packets` also contributed to raising the DDoS score, pointing to unusual bidirectional traffic patterns. Increased `Flow IAT Min` added to the DDoS score, reflecting rapid and frequent flow transitions. Lastly, a high `Fwd Packet Length Max` increased the DDoS score, showing large packet sizes typical in distributed attacks.  

Overall decision: The system classified the network flow as a DDoS attack based on the cumulative impact of these contributing factors.
```

### aud2-032

```
The classification of this flow as **Bot** is supported by several key features that align with the behavioral patterns of botnet traffic.

- **Init_Win_bytes_backward** increases the Bot score. This feature reflects the server's initial TCP window size, and a value of -1 typically indicates that the destination never completed a handshake, which is common in unanswered or refused probes—behavior often seen in botnet scanning or probing activities.

- **Init_Win_bytes_forward** also increases the Bot score. This represents the client's initial TCP window size. Unusual or fixed values here can be indicative of crafted traffic, such as that generated by bots, which may use specific fingerprints to evade detection or mimic legitimate traffic.

- **Fwd Header Length** increases the Bot score. A high header-to-p
```

### aud2-033

```
This flow was classified as **Bot** due to several unusual characteristics. The high **Bwd Header Length** (92.0) and **Fwd Header Length** (112.0) suggest abnormal packet structures, which are often seen in botnet traffic. Additionally, the **PSH Flag Count** is 1.0, indicating potential data transmission behavior typical of bots. The **Bwd IAT Std** (94,287.5) and **Fwd IAT Std** (82,023.5) show highly variable intervals between packets, a sign of irregular communication patterns associated with bot activity.
```

### aud2-034

```
Explanation:  
1. High Init_Win_bytes_backward significantly increased the DoS score by 2.8856.  
2. A long Idle Min further increased the DoS score by 1.0224.  
3. A high Idle Mean also contributed to the DoS score by 0.9044.  
4. An elevated FIN Flag Count added to the DoS score with a magnitude of 0.7171.  
5. Increased Bwd Packet Length Std provided additional support to the DoS score by 0.7091.  

The model predicted DoS based on the cumulative impact of these contributing factors.
```

### aud2-035

```
Explanation:  
The classification as a **Web Attack** is supported by several key features that align with the behavior of such attacks.  

- **Fwd IAT Min** increases the Web Attack score. A near-zero value indicates packet bursts, which are often characteristic of automated attack tools attempting to overwhelm a system.  
- **Max Packet Length** increases the Web Attack score. Small maxima suggest that the flow did not carry substantial data, which is typical of malicious traffic attempting to evade detection by using minimal, crafted payloads.  
- **Flow IAT Min** increases the Web Attack score. A near-zero minimum gap between consecutive packets suggests back-to-back bursts, a sign of flooding or scanning behavior commonly seen in web attacks.  
- **Flow Duration** decreases the Web Attack score. Un
```

### aud2-036

```
The flow was classified as **Bot** due to several unusual characteristics. A high **Bwd Header Length** (92.0) and **Fwd Header Length** (112.0) suggest abnormal packet structures often seen in botnet traffic. Additionally, the **Bwd IAT Std** (121104.5786) and **Fwd IAT Std** (105348.7249) indicate highly variable inter-arrival times, a common trait in automated bot activity. The **PSH Flag Count** (1.0) and **Flow Duration** (212037.0) also point to sustained, possibly coordinated, communication patterns typical of bot behavior.
```

### aud2-037

```
The model's prediction of **PortScan** is supported by the following features, each of which contributes to increasing the PortScan score:

- **Total Length of Fwd Packets** indicates a large volume of data being sent from the source to the destination, which is characteristic of active scanning or exfiltration behavior typical in PortScan attacks.
- **Init_Win_bytes_forward** reflects the client's initial TCP window size, which can reveal crafted traffic patterns often associated with scanning activities, as unusual or fixed values may indicate a lack of normal handshake behavior.
- **Flow Bytes/s** shows a high byte throughput, which is commonly linked to volumetric traffic patterns seen in PortScan, where a large number of packets are sent in a short period.
- **PSH Flag Count** reflects the
```

### aud2-038

```
The model classified this flow as FTP-Patator. The most influential factors were: 1. Total Length of Fwd Packets increased the FTP-Patator score (magnitude 4.1656); 2. Fwd PSH Flags increased the FTP-Patator score (magnitude 3.6462); 3. Fwd Packet Length Std increased the FTP-Patator score (magnitude 2.7371); 4. Packet Length Std decreased the FTP-Patator score (magnitude 1.3427); 5. Init_Win_bytes_forward increased the FTP-Patator score (magnitude 1.2817).
```

### aud2-039

```
The traffic in question was flagged as Bot due to a pattern of anomalies that align with the characteristics of botnet command-and-control or automated traffic. The initial server-side TCP window size, **Init_Win_bytes_backward**, was unusually high, which increased the Bot score, suggesting a potential refusal or incomplete handshake, a common sign of probing or scanning activity. This was further supported by the **Init_Win_bytes_forward**, which also increased the Bot score, indicating a client-side configuration that may be non-standard or crafted, often seen in automated tools. The **Fwd Header Length** was elevated, contributing to the Bot score, and this high header-to-payload ratio points to control-heavy traffic, such as scans or command transmissions typical of botnet communication. Additionally, the **Flow Bytes/s**
```

### aud2-040

```
The model classified this flow as DDoS. The most influential factors were: 1. act_data_pkt_fwd increased the DDoS score (magnitude 1.5998); 2. Init_Win_bytes_backward increased the DDoS score (magnitude 1.3344); 3. Fwd Packet Length Max increased the DDoS score (magnitude 1.2650); 4. Total Length of Fwd Packets increased the DDoS score (magnitude 1.2297); 5. Init_Win_bytes_forward decreased the DDoS score (magnitude 0.6668).
```

### aud2-041

```
The model predicts the class **DDoS** based on the following features, each of which contributes to increasing the DDoS score:

1. **act_data_pkt_fwd**: This feature indicates the presence of forward packets carrying actual payload data. A higher value suggests that data is being actively transmitted, which is characteristic of DDoS traffic where large volumes of data are sent to overwhelm a target.

2. **Bwd Packet Length Mean**: The mean size of backward packets is elevated, which can indicate responses to scan probes. In DDoS scenarios, such responses are common as attackers send probes and receive acknowledgments, contributing to the overall traffic volume.

3. **Init_Win_bytes_forward**: The client's initial TCP window size is non-zero and unusual, suggesting a crafted or non-standard handshake
```

### aud2-042

```
The model's prediction of **PortScan** is supported by the following features:

- **Total Length of Fwd Packets** increases the PortScan score. This feature reflects the total bytes sent from the source to the destination. A high value suggests bulk data transfer, which is characteristic of scanning activity where large packets are used to probe network resources.

- **Init_Win_bytes_forward** increases the PortScan score. This feature represents the client's initial TCP window size. Unusual or fixed values can indicate crafted traffic, such as that used in port scanning to fingerprint systems or evade detection.

- **Bwd Packets/s** increases the PortScan score. This feature measures the packet rate from the destination. A high forward rate with a low backward rate suggests one-sided traffic, which is typical
```

### aud2-043

```
The flow was classified as **Web Attack** due to the presence of **PSH Flag Count = 1.0**, which suggests potential payload manipulation, and **Subflow Fwd Packets = 3.0**, indicating fragmented or unusual packet behavior. Additionally, **Bwd Header Length = 40.0** and **Fwd Header Length = 104.0** suggest abnormal header sizes, which may indicate attempts to bypass security filters. These features collectively point toward suspicious network behavior consistent with a Web Attack.
```

### aud2-044

```
The flow was classified as **DoS** due to extremely high **Fwd Packets/s** and **Fwd Packets/s** values, indicating a massive rate of packets being sent in the forward direction, which is a common sign of a denial-of-service attack. The **Flow Packets/s** value of 666,666.67 suggests an abnormally high traffic rate, overwhelming the target system. Additionally, the **Fwd Packets/s** and **Fwd IAT Mean** values are unusually high, further supporting the detection of a potential DoS attack.
```

### aud2-045

```
Explanation:  
The classification as DDoS is supported by several key features that align with the behavior of distributed denial-of-service attacks.  

- **Bwd Packet Length Mean** increases the DDoS score. This feature reflects the mean size of backward packets, which are typically responses from the destination to the source. A high mean suggests significant traffic in this direction, which can indicate a large-scale attack where the destination is overwhelmed with responses.  
- **Packet Length Mean** increases the DDoS score. The average packet size across the entire flow being large suggests data transfer, which is characteristic of DDoS attacks where massive volumes of traffic are directed at a target.  
- **Init_Win_bytes_backward** increases the DDoS score. This feature indicates the server's initial TCP
```

### aud2-046

```
The model's prediction of **PortScan** is supported by the following features, each of which contributes to increasing the PortScan score:

- **Total Length of Fwd Packets** indicates bulk data transfer, which is characteristic of PortScan as it often involves large-scale probing or exfiltration.  
- **Init_Win_bytes_forward** reflects a crafted TCP handshake, which is commonly used in PortScan to identify and probe open ports.  
- **Flow Bytes/s** suggests high throughput, which aligns with volumetric traffic patterns typical of PortScan activities.  
- **PSH Flag Count** points to scripted, small-packet exchanges, a behavior often observed during PortScan to rapidly test multiple ports.  
- **Packet Length Mean** indicates small packet sizes, which are typical of
```

### aud2-047

```
Explanation:  
The classification as a **Web Attack** is supported by several key features.  

- **Fwd IAT Min** increases the Web Attack score. A near-zero value indicates packet bursts, which are characteristic of attack tools attempting to overwhelm a system.  
- **Max Packet Length** increases the Web Attack score. Small maxima suggest the flow never carried real data, which is typical of malicious traffic attempting to evade detection.  
- **Flow IAT Min** increases the Web Attack score. A near-zero minimum indicates back-to-back packet bursts, a sign of flooding behavior often seen in web attacks.  
- **Flow Duration** decreases the Web Attack score. Unusually short durations can indicate scanning or flooding, but the relatively moderate value here suggests the attack is not in its most
```

### aud2-048

```
The model predicts **Web Attack** based on the following features, each of which contributes to increasing the Web Attack score:

- **Fwd IAT Min** indicates a very short gap between consecutive packets from the source, suggesting packet bursts that are characteristic of attack tools attempting to overwhelm the target.
- **Max Packet Length** being small implies that the flow never carried real data, which is often seen in malicious traffic where the goal is to probe or disrupt rather than transmit meaningful content.
- **Flow IAT Min** is near-zero, indicating back-to-back packet bursts, a sign of flooding behavior typical in Web Attack scenarios.
- **Init_Win_bytes_backward** is -1, meaning the destination never completed a handshake, which is common in unanswered or refused probes, often associated with scanning or
```

### aud2-049

```
The model's prediction of **Bot** is supported by the following features, each contributing to the Bot score in the direction indicated:

- **Init_Win_bytes_backward** increases the Bot score. This feature reflects the server's initial TCP window size, where a value of -1 typically indicates a refused or unanswered probe, a common pattern in botnet traffic.
- **Bwd Packet Length Max** increases the Bot score. A large maximum packet size suggests substantive server responses, which can be indicative of coordinated or scripted interactions typical in bot activity.
- **Bwd IAT Std** increases the Bot score. High jitter in the destination's reply timing may signal abnormal or scripted exchanges, which are often observed in bot communications.
- **Init_Win_bytes_forward** increases the Bot score. This feature
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-025` to `aud2-049`, in one fenced block.