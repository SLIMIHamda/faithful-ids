# Extractor audit — annotation chunk 08 of 12

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


### aud2-175

```
The model predicts the DDoS class based on the following features, each of which contributes to increasing the DDoS score:

- **act_data_pkt_fwd**: This feature indicates the presence of forward packets carrying payload data. A non-zero value suggests actual data transmission, which is characteristic of sustained DDoS attacks where traffic is not limited to probes or handshakes.

- **Init_Win_bytes_forward**: This represents the client's initial TCP window size. Unusual or fixed values can signal crafted traffic, as they may indicate a lack of proper handshake, which is often seen in DDoS scenarios involving tool-fingerprinted traffic.

- **Total Backward Packets**: This feature counts the number of packets sent from the destination to the source. An asymmetry between forward and backward packets
```

### aud2-176

```
Explanation:  
The classification as **Bot** is supported by several key features that align with the behavioral patterns typical of botnet activity.  

- **Flow IAT Max** increases the Bot score, as large gaps between consecutive packets suggest idle-and-resume behavior, which is common in keep-alive or command-and-control channels used by bots.  
- **Bwd IAT Min** also increases the Bot score, as near-zero gaps between destination replies indicate rapid-fire responses, such as those seen in rejection storms or coordinated bot responses.  
- **Packet Length Mean** increases the Bot score, as small average packet sizes are often associated with control or probe traffic, which is characteristic of bot communication.  
- **Fwd IAT Max** increases the Bot score, as long pauses in the
```

### aud2-177

```
Explanation:  
The classification as **FTP-Patator** is supported by several key features that align with the behavior of this intrusion type.  

- **Max Packet Length** increases the FTP-Patator score. A large maximum packet size suggests the flow carried real data, which is consistent with active FTP attempts where data is transferred.  
- **Bwd Header Length** increases the FTP-Patator score. A high value here indicates header-only traffic in the backward direction, which may represent reset or acknowledgment packets, common in automated FTP probing.  
- **Fwd Packet Length Std** increases the FTP-Patator score. Low variability in forward packet sizes suggests uniform, machine-generated packets, a hallmark of automated tools like FTP-Patator used for brute-force attacks.  
- **Packet
```

### aud2-178

```
The model predicts the class **DoS** based on the following features, each of which contributes to increasing the DoS score:

1. **Init_Win_bytes_backward**: This feature increases the DoS score. A value of -1 indicates that the destination never completed a handshake, which is typical of unanswered or refused probes—a behavior commonly associated with DoS attacks.

2. **Idle Min**: This feature increases the DoS score. A shorter idle gap suggests rapid resumption of activity between bursts, which can indicate frequent and aggressive probing behavior characteristic of DoS attacks.

3. **Idle Mean**: This feature increases the DoS score. A long mean idle gap between activity bursts is characteristic of periodic beaconing and keep-alive command channels, which are often used in sustained DoS activities.
```

### aud2-179

```
The traffic in question closely aligns with the class profile of SSH-Patator, a brute-force credential guessing attack against SSH services. The evidence begins with the **Bwd Header Length**, which increases the SSH-Patator score by a significant magnitude of 4.8244. This suggests that the traffic involves a high volume of header-only reply streams in the backward direction, likely indicating acknowledgment or reset traffic without actual content—common in automated probing or failed login attempts. Next, the **Total Length of Bwd Packets** also increases the score by 4.3185, pointing to near-zero replies against non-trivial forward traffic, which may reflect unanswered probes or refused services, further supporting the idea of a systematic attempt to guess credentials. As the story unfolds,
```

### aud2-180

```
Explanation:  
The classification as **FTP-Patator** is supported by several key features that align with the behavior of this intrusion-detection class.  

- **Total Length of Fwd Packets** increases the FTP-Patator score. This feature indicates a large volume of data being sent from the source to the destination, which is consistent with bulk upload or exfiltration activities commonly associated with FTP-Patator.  
- **Fwd PSH Flags** also increases the FTP-Patator score. A high count of TCP PSH flags suggests that the source is pushing data on every small packet, a behavior typical of interactive tools and credential-stuffing clients, which are characteristic of FTP-Patator.  
- **Fwd Packet Length Std** increases the FTP-Patator
```

### aud2-181

```
The traffic in question closely aligns with the class profile of PortScan, as it exhibits a pattern of reconnaissance through many short, small, one-sided flows. The evidence begins with the **Total Length of Fwd Packets**, which increases the PortScan score—this suggests a large volume of data being sent from the source to the destination, potentially indicating a probing phase where the attacker is testing open ports or exfiltrating data. This is further supported by **Bwd Packets/s**, which also increases the score, but at a lower magnitude; the low backward packet rate against a high forward rate points to one-sided communication, a hallmark of scanning activity. The **Init_Win_bytes_forward** feature, which also increases the score, reveals a non-standard initial TCP window size, a common
```

### aud2-182

```
Explanation:  
The highest contributing factor was Fwd IAT Min, which increased the Web Attack score by 2.0963. Next, Flow IAT Min also increased the score by 2.0652. Then, Init_Win_bytes_backward raised the score by 1.8742. Following this, Init_Win_bytes_forward contributed an increase of 1.1753. Lastly, min_seg_size_forward added 0.8576 to the score.  
Overall decision: The combination of these factors significantly increased the Web Attack score, leading to the prediction of a Web Attack.
```

### aud2-183

```
The traffic in question closely aligns with the class profile of PortScan, as it exhibits a pattern of reconnaissance probing across multiple ports, characterized by many short, small, one-sided flows. The evidence begins with the **Total Length of Fwd Packets**, which increases the PortScan score—this suggests a large volume of data being sent from the source to the destination, potentially indicating a bulk upload or exfiltration, but in this case, the high magnitude points to a more probing behavior, consistent with scanning activity. The **Init_Win_bytes_forward** also increases the score, revealing an unusual initial TCP window size, a signature often associated with crafted traffic or a specific tool fingerprint, further hinting at non-standard, possibly malicious behavior. As the flow continues, the **Flow Bytes/s
```

### aud2-184

```
The model predicts the class as **BENIGN**, supported by the following features:

1. **Init_Win_bytes_backward** increases the BENIGN score. This feature reflects the server's initial TCP window size, and a value of -1 (indicative of a failed handshake) is typical of unanswered or refused probes, which are benign in nature.

2. **Total Backward Packets** increases the BENIGN score. This feature counts the number of packets sent from the destination to the source. Asymmetry with forward packets can indicate one-sided traffic, which is often seen in benign probe or scan activities.

3. **Fwd Packet Length Max** increases the BENIGN score. This feature represents the largest packet sent by the source. Small maxima suggest no real payload was carried,
```

### aud2-185

```
The traffic in question exhibits characteristics strongly aligned with the class profile of PortScan, a form of reconnaissance where an attacker probes multiple ports to identify open services. The evidence begins with the **Total Length of Foward Packets**, which increases the PortScan score—this suggests a large volume of data being sent from the source to the destination, consistent with a probing behavior that may involve scanning or testing various services. Complementing this is the **Init_Win_bytes_forward**, which also increases the score; this feature reflects the client's initial TCP window size, and its unusual or fixed values often indicate crafted traffic, such as that seen in automated scans. The **Bwd Packets/s** further increases the score, highlighting a low rate of packets being sent from the destination back to the source,
```

### aud2-186

```
Explanation:  
The classification as **PortScan** is supported by several key features that align with the behavior of scanning activity.  

- **Total Length of Fwd Packets** increases the PortScan score, as very large totals suggest bulk data transfer, which is often associated with exfiltration during a scan.  
- **Flow IAT Mean** increases the PortScan score, with very small values indicating flooding, a common characteristic of scanning traffic.  
- **Flow IAT Min** increases the PortScan score, as near-zero minima suggest back-to-back packet bursts, typical of flood-based scanning.  
- **Init_Win_bytes_forward** increases the PortScan score, as unusual fixed values may indicate a crafted handshake, a sign of automated or malicious traffic.  
- **PS
```

### aud2-187

```
The model classified this flow as Bot. The most influential factors were: 1. Init_Win_bytes_backward increased the Bot score (magnitude 3.1951); 2. Bwd IAT Min increased the Bot score (magnitude 3.0518); 3. Flow IAT Max increased the Bot score (magnitude 2.5033); 4. Fwd IAT Max increased the Bot score (magnitude 1.6841); 5. Bwd Packet Length Max increased the Bot score (magnitude 1.6075).
```

### aud2-188

```
The model classified this flow as Web Attack. The most influential factors were: 1. Fwd IAT Min increased the Web Attack score (magnitude 6.3516); 2. Max Packet Length increased the Web Attack score (magnitude 4.7387); 3. Flow Duration decreased the Web Attack score (magnitude 1.4443); 4. Flow IAT Min increased the Web Attack score (magnitude 1.3158); 5. Init_Win_bytes_backward decreased the Web Attack score (magnitude 0.8767).
```

### aud2-189

```
The flow was classified as **Bot** due to high **Bwd Packets/s** (25,641.03) and **Flow Packets/s** (51,282.05), indicating a high rate of packets in both directions, which is unusual for normal traffic. Additionally, the **Flow Duration** (39.0) and **Flow IAT Std** (0.0) suggest a very short and consistent interval between packets, typical of automated or bot-driven activity. The **URG Flag Count** (1.0) and **ACK Flag Count** (1.0) also point to potential abnormal signaling behavior.
```

### aud2-190

```
SHAP attribution (top-5) for class Bot: Init_Win_bytes_backward=+5.0289; Init_Win_bytes_forward=+3.5115; Fwd Header Length=+1.9376; Flow Bytes/s=+1.0307; Fwd Packets/s=+0.5474
```

### aud2-191

```
The flow was classified as **SSH-Patator** due to high **Bwd Packets/s** (13,888.89) and **Flow Packets/s** (27,777.78), indicating a high rate of packets in both directions, which is characteristic of automated brute-force attacks. The **Flow Duration** of 72 seconds and **Flow IAT Mean** of 72 seconds suggest a sustained, continuous flow, typical of mass connection attempts. Additionally, the **Bwd Header Length** of 32.0 and **Fwd Header Length** of 32.0 indicate consistent header sizes, often seen in scripted attacks like SSH-Patator.
```

### aud2-192

```
Explanation:  
The classification of this flow as **BENIGN** is supported by several key features that align with characteristics of normal, machine-generated traffic.  

- **Max Packet Length** increases the BENIGN score, as a small maximum packet size suggests the flow did not carry large volumes of real data, which is typical of benign traffic.  
- **Packet Length Std** also increases the BENIGN score, indicating low variability in packet sizes, a sign of uniform, automated traffic rather than irregular or malicious behavior.  
- **Init_Win_bytes_forward** increases the BENIGN score, as a fixed, unusual initial window size can be a fingerprint of legitimate tools or stacks, suggesting no malicious handshake anomalies.  
- **Bwd Packets/s** increases the BENIGN score, as a
```

### aud2-193

```
The prediction of **FTP-Patator** is supported by the following features, each contributing to the score in a specific way:

- **Max Packet Length** increases the FTP-Patator score. This suggests that the flow involves relatively large packets, which may indicate the transmission of data typical in brute-force attacks, such as those seen in FTP-Patator.
  
- **Bwd Header Length** increases the FTP-Patator score. A high value here implies that the backward direction of the flow consists largely of header bytes, which may indicate acknowledgment or reset traffic without content—common in automated probing or scanning behavior associated with FTP-Patator.

- **Fwd Packet Length Std** increases the FTP-Patator score. A low variability in forward packet sizes suggests uniform packet generation, a
```

### aud2-194

```
The model predicts **PortScan** based on the following features:

- **Total Length of Fwd Packets** increases the PortScan score. This feature indicates bulk data transfer, which is characteristic of scanning activity where large amounts of data are sent to probe network responses.
- **Flow IAT Mean** increases the PortScan score. A highly regular interval between packets suggests automated or scripted traffic, which aligns with the behavior of port scanning tools.
- **Flow IAT Min** increases the PortScan score. A near-zero minimum interval between packets indicates back-to-back bursts, a sign of flooding or rapid scanning activity.
- **Init_Win_bytes_forward** increases the PortScan score. This feature reflects the client's initial TCP window size, which can reveal crafted traffic patterns, such as those
```

### aud2-195

```
The model predicts the class **DoS** based on the following features:

- **Init_Win_bytes_forward** increases the DoS score. This feature reflects the client's initial TCP window size, which can reveal crafted traffic through unusual, fixed values. Such values are often indicative of a malicious handshake, aligning with the characteristics of a Denial of Service attack.

- **Average Packet Size** increases the DoS score. A large average packet size suggests content transfer, which is consistent with the data-intensive behavior observed in DoS attacks, where the attacker floods the network with large volumes of traffic.

- **Bwd Packets/s** increases the DoS score. A low backward packet rate relative to a high forward rate indicates one-sided traffic, which is typical of attack traffic where the destination
```

### aud2-196

```
The traffic in question was classified as a DDoS attack due to a pattern of behavior that aligns closely with the class profile of distributed denial-of-service attacks, which are characterized by volumetric traffic from many sources. The evidence begins with **act_data_pkt_fwd**, which increases the DDoS score—this suggests that the flow involved actual data transmission rather than just handshake or probe traffic, indicating real payload activity, a hallmark of coordinated attacks. Supporting this, **Init_Win_bytes_forward** also increases the score, pointing to a client-side configuration that may be indicative of crafted or automated traffic, as unusual initial window sizes are often used to mask or accelerate attack vectors. Meanwhile, **Total Backward Packets** further raises the DDoS score, highlighting an asymmetry in the direction
```

### aud2-197

```
SHAP attribution (top-5) for class Web Attack: Fwd IAT Min=+7.2361; Max Packet Length=+4.7808; Flow IAT Min=+2.1648; Init_Win_bytes_backward=+1.0627; Flow Duration=+0.8855
```

### aud2-198

```
The traffic in question exhibits characteristics that align closely with a DDoS attack, as evidenced by several key features that collectively suggest a coordinated effort to overwhelm a target system with volumetric traffic. The first indicator is the **Init_Win_bytes_backward**, which increases the DDoS score, suggesting that the destination system never completed a proper handshake, a common pattern in unanswered or refused probes often seen in DDoS scenarios. This points to a flood of traffic that does not establish meaningful connections, a hallmark of distributed attacks. Complementing this is the **act_data_pkt_fwd**, which also increases the DDoS score, indicating that the forward packets carry actual data, further reinforcing the presence of real traffic rather than mere probes. Meanwhile, the **Bwd Packet Length Mean** contributes to the
```

### aud2-199

```
The prediction of **SSH-Patator** is supported by the following features, each of which contributes to increasing the score for this class:

1. **Bwd Header Length**: The increase in this feature suggests the presence of header-only reply streams, which are characteristic of acknowledgment or reset traffic without content. This is consistent with the behavior of SSH-Patator, which often involves automated probing and response patterns that generate such traffic.

2. **Total Length of Bwd Packets**: The high magnitude indicates near-zero replies against non-trivial forward traffic, which may suggest unanswered probes or refused services. This aligns with the nature of SSH-Patator, which frequently attempts multiple login credentials and may receive no response or minimal responses from targets.

3. **Fwd Packet Length Std**: A near
```

---

Now output exactly 25 JSONL lines, one per item above, from `aud2-175` to `aud2-199`, in one fenced block.