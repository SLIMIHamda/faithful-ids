# Extractor audit — annotation chunk 11 of 12

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


### aud2-250

```
The traffic in question exhibits characteristics that align closely with the profile of benign activity. The initial TCP window size on the client side, **Init_Win_bytes_forward**, is notably high, which increases the BENIGN score and suggests a properly established and tool-agnostic connection, as this value is typically consistent with normal handshake behavior. Similarly, the server's initial TCP window size, **Init_Win_bytes_backward**, also contributes positively to the BENIGN score, reinforcing the idea of a completed and legitimate handshake rather than an attempted probe or refused connection. The **Average Packet Size** is moderate, further increasing the BENIGN score and pointing to traffic that is neither overly control-heavy nor data-intensive, which is typical of normal communication. The **Fwd Header Length** is relatively low, adding to the BEN
```

### aud2-251

```
Explanation:  
The classification as **FTP-Patator** is supported by several key features that align with the behavior of this intrusion type.  

- **Max Packet Length** increases the FTP-Patator score. A large maximum packet size suggests the flow carried real data, which is consistent with active FTP attempts where data is transferred.  
- **Bwd Header Length** increases the FTP-Patator score. A high value here indicates header-only traffic in the backward direction, which may represent reset or acknowledgment packets, common in automated FTP probing.  
- **Fwd Packet Length Std** increases the FTP-Patator score. Low variability in forward packet sizes suggests uniform, machine-generated packets, a hallmark of automated tools like FTP-Patator used for brute-force attacks.  
- **Packet
```

### aud2-252

```
The traffic in question was classified as a denial-of-service (DoS) attack due to a pattern of behavior that aligns closely with the characteristics of an HTTP flood attack, which is defined by high-volume, high-rate flows designed to overwhelm a server. The evidence begins with **Init_Win_bytes_backward**, which increases the DoS score and suggests that the destination system never completed a proper handshake, a common sign of unanswered or refused probes—typical in a DoS scenario where the server is being bombarded with traffic without establishing legitimate connections. This sets the stage for a coordinated attack, where the server is not engaging in normal communication. 

Next, **Idle Mean** also increases the DoS score, indicating long, regular intervals of inactivity between bursts of activity. This pattern is characteristic
```

### aud2-253

```
The flow was classified as **PortScan** due to high **Bwd Packets/s** (17,857.14) and **Flow Packets/s** (35,714.29), indicating a high rate of packets sent in the backward direction, which is typical of scanning behavior. Additionally, **Flow Duration** (56.0) and **Flow IAT Mean** (56.0) suggest a short, rapid sequence of packets, consistent with scanning activity. The **PSH Flag Count** (1.0) also contributes, as it indicates packet segmentation, often seen in port scanning.
```

### aud2-254

```
The traffic in question exhibits characteristics strongly aligned with Botnet command-and-control activity, as evidenced by several key features that collectively suggest a scripted, automated exchange rather than a natural user session. The first and most prominent indicator is the high value of **Init_Win_bytes_backward**, which increases the Bot score and suggests that the destination never completed a proper handshake, a common sign of unanswered or refused probes—behavior typical of automated scanning or probing by a bot. This is further reinforced by **Bwd Packet Length Max**, which also increases the Bot score, indicating that the destination sent large packets, suggesting substantive server responses rather than simple error or reset replies, a pattern often seen in coordinated botnet communications. Meanwhile, **Bwd IAT Std**—the jitter in the destination's reply timing—also
```

### aud2-255

```
The prediction of **FTP-Patator** is supported by the following features, each contributing to the score in a specific way:

- **Max Packet Length** increases the FTP-Patator score. This suggests that the flow involves relatively large packets, which is characteristic of FTP traffic where data is transferred in larger chunks, as opposed to small, fragmented packets typical of benign traffic.

- **Bwd Header Length** increases the FTP-Patator score. A high value here indicates that the backward direction of the flow consists largely of TCP/IP headers, which may suggest header-only replies—common in FTP responses or reset traffic, often associated with automated probing or scanning behavior.

- **Fwd Packet Length Std** increases the FTP-Patator score. A low variability in forward packet sizes indicates uniform packet
```

### aud2-256

```
The traffic in question was classified as Bot due to a pattern of behavior that aligns closely with the characteristics of a botnet command-and-control communication. The initial server-side TCP window size, **Init_Win_bytes_backward**, was notably high, which increased the Bot score and suggests that the destination system was responding with a large initial window, a behavior often seen in automated or scripted interactions rather than organic user sessions. This is further supported by the **Bwd IAT Std**, which also increased the Bot score—indicating a highly regular and predictable timing pattern in the destination's replies, a hallmark of scripted or automated exchanges rather than human-driven conversations. Meanwhile, the **Init_Win_bytes_forward**, which measures the client's initial TCP window size, also contributed positively to the Bot score, pointing
```

### aud2-257

```
Explanation:  
1. A high value in Init_Win_bytes_forward significantly increased the DoS score by 3.1595.  
2. Fwd Packets/s further increased the DoS score by 1.4043.  
3. Average Packet Size contributed to the DoS score with an increase of 1.1826.  
4. Bwd Packets/s added to the DoS score, increasing it by 1.0940.  
5. Flow IAT Min also raised the DoS score by 0.7441.  

The combination of these factors led to the prediction of a DoS attack.
```

### aud2-258

```
The model predicts the class **DoS** based on the following features, each of which contributes to increasing the DoS score:

1. **Init_Win_bytes_backward**: This feature increases the DoS score. A value of -1 indicates that the destination never completed a handshake, which is typical of unanswered or refused probes—a behavior commonly associated with Denial of Service attacks.

2. **Idle Min**: This feature increases the DoS score. A shorter idle gap suggests rapid resumption of activity between bursts, which can indicate frequent and coordinated traffic patterns often seen in DoS attacks.

3. **Idle Mean**: This feature increases the DoS score. A long mean idle gap between activity bursts is characteristic of periodic beaconing or keep-alive command channels, behaviors that may be used to maintain
```

### aud2-259

```
The traffic in question closely aligns with the class profile of FTP-Patator, a brute-force credential guessing attack, as evidenced by the pattern of features that together suggest a coordinated, automated attempt to guess valid FTP credentials. The attack begins with a high **Max Packet Length**, which increases the FTP-Patator score, indicating that the flow involved relatively large packets—suggesting the transmission of actual data rather than simple control or probe traffic. This is further reinforced by the **Bwd Header Length**, which also increases the score, pointing to a stream of header-only replies in the backward direction, likely acknowledgments or reset responses that lack meaningful content, a common pattern in automated scanning. The **Packet Length Std** is near-zero, increasing the score, which implies that the packet sizes are highly
```

### aud2-260

```
Explanation:  
The classification as **PortScan** is supported by several key features that align with the behavior of scanning activity.  

- **Total Length of Fwd Packets** increases the PortScan score, as very large totals suggest bulk data transfer, which is characteristic of scanning behavior.  
- **Init_Win_bytes_forward** increases the PortScan score, indicating potential crafted traffic through unusual initial window sizes, which are often used in fingerprinting or scanning attempts.  
- **Flow Bytes/s** increases the PortScan score, as high throughput is commonly associated with volumetric traffic, which can be a sign of scanning or probing.  
- **PSH Flag Count** increases the PortScan score, as elevated counts on small packets suggest scripted, rapid exchanges typical of scanning or probing.
```

### aud2-261

```
Explanation:  
The classification as **DoS** is supported by several key features.  

- **Init_Win_bytes_forward** increases the DoS score because unusual fixed values in this field can indicate a crafted traffic pattern, often associated with malicious fingerprinting or tool-based attacks.  
- **Fwd Packets/s** increases the DoS score as a high packet rate from the source suggests flooding or aggressive scanning behavior, which is characteristic of denial-of-service attacks.  
- **Average Packet Size** increases the DoS score because a large average indicates content transfer, which can be a sign of overwhelming the target with data, a common tactic in DoS attacks.  
- **Bwd Packets/s** increases the DoS score since a low backward packet rate relative to a high forward rate
```

### aud2-262

```
The model classified this flow as BENIGN. The most influential factors were: 1. Init_Win_bytes_backward increased the BENIGN score (magnitude 1.8986); 2. Total Backward Packets increased the BENIGN score (magnitude 1.0733); 3. Fwd Packet Length Max increased the BENIGN score (magnitude 0.6455); 4. Active Min increased the BENIGN score (magnitude 0.6024); 5. Fwd IAT Std increased the BENIGN score (magnitude 0.4211).
```

### aud2-263

```
Explanation:  
1. A high Flow IAT Max significantly increased the Bot score by 2.7810.  
2. A high Bwd IAT Min further increased the Bot score by 2.7558.  
3. A high Packet Length Mean added to the Bot score with a magnitude of 1.3747.  
4. A high Fwd IAT Max contributed to the Bot score by 1.0987.  
5. A high Flow Bytes/s slightly decreased the Bot score by 0.6035.  

The model predicted **Bot** based on the cumulative effect of these contributing factors.
```

### aud2-264

```
The traffic in question was flagged as a DDoS attack due to a pattern of behavior that aligns closely with the class profile of distributed denial-of-service: a surge in volumetric traffic originating from multiple sources. The evidence begins with **act_data_pkt_fwd**, which shows a significant increase in the number of forward packets carrying actual payload data, suggesting that the flow is not just a handshake or probe but is actively transmitting content—this contributes to the DDoS score by indicating real data transfer, a hallmark of sustained attack traffic. Next, **Bwd Packet Length Mean** is also elevated, pointing to responses that are not minimal or near-zero, which could imply that the system is being flooded with replies, further amplifying the attack volume. The **Init_Win_bytes_forward** feature,
```

### aud2-265

```
Explanation:  
The Total Length of Fwd Packets significantly increased the PortScan score by 2.0947.  
The Init_Win_bytes_forward further increased the PortScan score by 1.2823.  
The Flow Bytes/s contributed to the PortScan score with an increase of 1.0561.  
The PSH Flag Count added to the PortScan score with an increase of 1.0053.  
The Packet Length Mean also increased the PortScan score by 0.7656.  

Overall decision: The network flow was classified as PortScan due to the cumulative increase in the score from these contributing factors.
```

### aud2-266

```
The flow was classified as **BENIGN** due to its low activity and minimal data transfer characteristics. The **Bwd Packets/s** value of 20408.16 indicates a high rate of backward packets, which may suggest normal traffic patterns. Additionally, **Flow Duration** and **Flow Packets/s** show a short, steady flow with consistent packet rates, typical of benign behavior. Most statistical features (e.g., **Active Mean**, **Fwd IAT Std**) are zero, indicating no unusual variability or anomalies. These features collectively suggest a regular, non-malicious network interaction.
```

### aud2-267

```
Explanation:  
The highest contributing factor was Max Packet Length, which increased the FTP-Patator score by 6.3059. Next, Bwd Header Length also increased the score by 5.8738. Packet Length Std further increased the score by 0.9814. Average Packet Size added another 0.7531 to the score. However, Flow Duration decreased the score by 0.7240.  
Overall decision: The network flow was classified as FTP-Patator due to the cumulative effect of these contributing factors.
```

### aud2-268

```
The flow was classified as **DDoS** due to several anomalous features. A very high **Flow Duration** (77,768,226.0) and **Flow IAT Max** (66,800,000.0) suggest an extended, potentially sustained attack. The **Bwd IAT Std** (390,111.5972) and **Fwd IAT Std** (24,900,000.0) indicate highly variable intervals between packets, a common pattern in DDoS traffic. Additionally, the **Bwd Packet Length Std** (2,538.919) and **Packet Length Std** (1,804.
```

### aud2-269

```
The traffic in question closely aligns with the class profile of SSH-Patator, a brute-force credential guessing attack against SSH. The evidence begins with **Init_Win_bytes_forward**, which increases the SSH-Patator score by a significant magnitude of 5.0303. This feature reflects the client's initial TCP window size, and its unusual fixed value suggests a crafted connection, possibly from a tool attempting to fingerprint the target. The **Init_Win_bytes_backward** also increases the score, with a magnitude of 4.4092, indicating the server's initial window size. A value of -1 here is typical of unanswered or refused probes, further supporting the idea of a one-sided, probing attack. The **URG Flag Count** adds to the score with
```

### aud2-270

```
The classification of this flow as **Bot** is supported by several key features that align with the behavioral patterns of botnet activity:

- **Init_Win_bytes_backward** increases the Bot score. This feature reflects the server's initial TCP window size, and a value of -1 typically indicates that the destination never completed a handshake, which is common in unanswered or refused probes—behavior often seen in botnet scanning or probing activities.

- **Init_Win_bytes_forward** also increases the Bot score. This represents the client's initial TCP window size. Unusual or fixed values here can be indicative of crafted traffic, such as that generated by malicious tools, which often lack proper handshakes, a hallmark of botnet communication.

- **Fwd Header Length** raises the Bot score. A high
```

### aud2-271

```
The classification of this traffic as **Bot** is supported by several key features that align with the behavioral patterns typical of automated or scripted network activity.

- **Init_Win_bytes_backward** increases the Bot score. This feature reflects the server's initial TCP window size, and a value of -1 suggests the destination never completed a handshake, which is common in unanswered or refused probes—behavior often seen in bot-driven traffic.
  
- **Bwd Packet Length Max** increases the Bot score. A large maximum packet size indicates substantive server responses, which may suggest a coordinated exchange. However, in the context of bot activity, such responses can be part of a scripted or automated interaction, distinguishing it from organic user-initiated sessions.

- **Bwd IAT Std** increases the Bot score. This feature
```

### aud2-272

```
The flow was classified as **SSH-Patator** due to high **Bwd Packets/s** (13,333.33) and **Flow Packets/s** (26,666.67), indicating a high rate of packets in the backward direction, which is characteristic of automated brute-force attacks. The **Bwd Header Length** of 32.0 suggests a consistent packet structure typical of SSH traffic. Additionally, the **Flow Duration** of 75.0 seconds and **Flow IAT Mean** of 75.0 seconds indicate a sustained, repetitive flow pattern, further aligning with SSH-Patator behavior.
```

### aud2-273

```
The flow was classified as **Bot** due to several unusual characteristics. The **Bwd Header Length** is unusually high at 60.0, suggesting potential malicious traffic manipulation. Additionally, the **Bwd IAT Mean** and **Bwd IAT Std** are significantly elevated, indicating irregular timing patterns typical of botnet activity. The **PSH Flag Count** is 1.0, which is non-zero and may signal abnormal packet behavior. These features collectively suggest coordinated, automated traffic patterns consistent with bot activity.
```

### aud2-274

```
The traffic in question closely aligns with the class profile of FTP-Patator, a brute-force credential guessing attack against an FTP server. The evidence points to a coordinated attempt to exhaustively guess valid login credentials through repeated, systematically varied packet exchanges. The largest contributing factor was the **Max Packet Length**, which increased the FTP-Patator score—suggesting that the flow involved relatively large packets, indicative of actual data transfer rather than minimal header-only traffic, which would be typical of a small or non-functional connection. This implies the attack was not just a probe but an active attempt to interact with the server. The **Bwd Header Length** also increased the score, pointing to a pattern of header-only responses in the backward direction, which is characteristic of automated or machine-generated traffic, such as
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-250` to `aud2-274`, in one fenced block.