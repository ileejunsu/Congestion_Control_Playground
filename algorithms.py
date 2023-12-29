import random

class CongestionControlAlgorithm:
    def __init__(self, cwnd, ssthresh, rtt, mss, rto, duplicate_acks, loss_rate, bandwidth, queue_size):
        # Initialization of properties
        self.cwnd = cwnd
        self.ssthresh = ssthresh
        self.rtt = rtt
        self.mss = mss
        self.rto = rto
        self.duplicate_acks = duplicate_acks
        self.loss_rate = loss_rate
        self.bandwidth = bandwidth
        self.queue_size = queue_size
        self.simulation_duration = 100
        self.time_step = 1
        self.state = 'Initial'

    def packet_loss_occurred(self, time):
        return self.loss_rate > 0 and random.random() < self.loss_rate

  
    def record_state_transition(self, state_transitions, time, state, cwnd, ssthresh, event=None):
        """Record the state transition with additional details like cwnd and ssthresh.
           If an event occurs (e.g., packet loss), it is recorded as well."""
        last_record = state_transitions[-1] if state_transitions else None
        if not last_record or last_record['state'] != state or event:
            transition = {
                'time': time, 
                'state': state, 
                'cwnd': cwnd, 
                'ssthresh': ssthresh
            }
            if event:
                transition['event'] = event
            state_transitions.append(transition)
        else:
            # Update time and other parameters of the last state if no change in state
            last_record.update({'time': time, 'cwnd': cwnd, 'ssthresh': ssthresh})

    def simulate_queue_length_variation(self):
        traffic_factor = random.uniform(0.8, 1.2)
        queue_variation = self.cwnd * traffic_factor
        self.queue_size = max(min(queue_variation, self.queue_size), 0)
        return self.queue_size

    def simulate_acknowledgments(self):
        acks_received = self.cwnd / self.rtt
        return acks_received

    def perform_algorithm(self):
        raise NotImplementedError("This method should be implemented by subclasses")
    
class Tahoe(CongestionControlAlgorithm):
    def perform_algorithm(self):
        simulation_results = []
        packet_loss_events = []
        rtt_variations = []
        state_transitions = []
        queue_lengths = []
        acks_list = []

        # Assume a base RTT without congestion
        base_rtt = self.rtt

        for t in range(0, self.simulation_duration, self.time_step):
            # Simulate RTT fluctuation due to congestion, but not less than base RTT
            current_rtt = max(base_rtt, self.rtt + random.uniform(-0.1 * self.rtt, 0.1 * self.rtt))
            rtt_variations.append({'time': t, 'rtt': current_rtt})

            # Detect packet loss
            packet_loss = self.packet_loss_occurred(t)
            event = None
            if packet_loss:
                state = 'Loss Detected'
                event = 'Packet Loss'
                packet_loss_events.append({'time': t, 'event': 'Packet Loss'})
                self.cwnd = 1  # TCP Tahoe resets cwnd to 1 on packet loss
                self.ssthresh = max(int(self.cwnd / 2), 2)  # Avoid ssthresh becoming less than 2*MSS
            elif self.cwnd < self.ssthresh:
                state = 'Slow Start'
                self.cwnd += 1  # Exponential growth
            else:
                state = 'Congestion Avoidance'
                self.cwnd += max(1, int(self.mss * self.mss / self.cwnd))  # Linear growth

            self.record_state_transition(state_transitions, t, state, self.cwnd, self.ssthresh, event)

            # Calculate throughput as min(bandwidth or window size / RTT)
            throughput = min(self.bandwidth, (self.cwnd * self.mss) / current_rtt)

            queue_length = self.simulate_queue_length_variation()
            acks = self.simulate_acknowledgments()

            queue_lengths.append(queue_length)
            acks_list.append(acks)

            simulation_results.append({
                'time': t,
                'cwnd': self.cwnd,
                'rtt': current_rtt,
                'throughput': throughput,
                'state': state,
                'queue_length': queue_length,
                'acks': acks
            })

        return simulation_results, packet_loss_events, rtt_variations, state_transitions, queue_lengths, acks_list

    
class Reno(CongestionControlAlgorithm):
    def perform_algorithm(self):
        simulation_results = []
        packet_loss_events = []
        rtt_variations = []
        state_transitions = []
        state = 'Slow Start'
        duplicate_ack_count = 0
        queue_lengths = []
        acks_list = []

        for t in range(0, self.simulation_duration, self.time_step):
            packet_loss = self.packet_loss_occurred(t)
            event = None

            if duplicate_ack_count >= 3:
                state = 'Fast Recovery'
                event = 'Packet Loss'
                self.ssthresh = max(int(self.cwnd / 2), 1)
                self.cwnd = self.ssthresh + 3 * self.mss
                duplicate_ack_count = 0  # Reset duplicate acknowledgment count
                packet_loss_events.append({'time': t, 'event': 'Packet Loss'})  # Record the packet loss event
            elif packet_loss:
                state = 'Fast Retransmit'
                self.ssthresh = max(int(self.cwnd / 2), 1)
                self.cwnd = self.ssthresh + 3 * self.mss
                duplicate_ack_count = 0  # Reset duplicate acknowledgment count
                packet_loss_events.append({'time': t, 'event': 'Packet Loss'})  # Record the packet loss event
            else:
                if self.cwnd < self.ssthresh:
                    state = 'Slow Start'
                    self.cwnd += 1
                else:
                    state = 'Congestion Avoidance'
                    self.cwnd += max(1, int(self.mss * self.mss / self.cwnd))

            self.record_state_transition(state_transitions, t, state, self.cwnd, self.ssthresh, event)

            if packet_loss:
                duplicate_ack_count += 1

            current_rtt = self.rtt + random.uniform(-5, 5)
            rtt_variations.append({'time': t, 'rtt': current_rtt})
            throughput = self.cwnd / current_rtt
            queue_length = self.simulate_queue_length_variation()
            acks = self.simulate_acknowledgments()

            queue_lengths.append(queue_length)
            acks_list.append(acks)

            simulation_results.append({'time': t, 'cwnd': self.cwnd, 'rtt': current_rtt,
                                       'throughput': throughput, 'state': state,
                                       'queue_length': queue_length, 'acks': acks})

        return simulation_results, packet_loss_events, rtt_variations, state_transitions, queue_lengths, acks_list

    
class Cubic(CongestionControlAlgorithm):
    def perform_algorithm(self):
        simulation_results = []
        packet_loss_events = []
        rtt_variations = []
        state_transitions = []
        state = 'Congestion Avoidance'
        Wmax = self.cwnd
        cubic_beta = 0.7
        last_congestion_time = 0
        queue_lengths = []
        acks_list = []

        for t in range(0, self.simulation_duration, self.time_step):
            packet_loss = self.packet_loss_occurred(t)
            event = None
            if packet_loss:
                state = 'Fast Recovery'
                event = 'Packet Loss'
                Wmax = self.cwnd
                self.cwnd = max(int(self.cwnd * cubic_beta), 1)
                last_congestion_time = t
                packet_loss_events.append({'time': t, 'event': 'Packet Loss'})
            else:
                time_since_last_congestion = t - last_congestion_time
                self.cwnd = int(Wmax * (1 - cubic_beta)) + time_since_last_congestion ** 3

            self.record_state_transition(state_transitions, t, state, self.cwnd, self.ssthresh, event)

            current_rtt = self.rtt + random.uniform(-5, 5)
            rtt_variations.append({'time': t, 'rtt': current_rtt})
            throughput = self.cwnd / current_rtt
            queue_length = self.simulate_queue_length_variation()
            acks = self.simulate_acknowledgments()

            queue_lengths.append(queue_length)
            acks_list.append(acks)

            simulation_results.append({'time': t, 'cwnd': self.cwnd, 'rtt': current_rtt,
                                       'throughput': throughput, 'state': state,
                                       'queue_length': queue_length, 'acks': acks})

        return simulation_results, packet_loss_events, rtt_variations, state_transitions, queue_lengths, acks_list


class BICTCP(CongestionControlAlgorithm):
    def perform_algorithm(self):
        simulation_results = []
        packet_loss_events = []
        rtt_variations = []
        state_transitions = []
        state = 'Slow Start'
        Wmax = self.cwnd
        bic_beta = 0.8
        bic_K = 0
        low_window_threshold = 10
        queue_lengths = []
        acks_list = []

        for t in range(0, self.simulation_duration, self.time_step):
            packet_loss = self.packet_loss_occurred(t)
            event = None
            if packet_loss:
                state = 'Fast Recovery'
                event = 'Packet Loss'
                Wmax = self.cwnd
                self.cwnd = max(int(self.cwnd * bic_beta), 1)
                bic_K = ((Wmax - self.cwnd) / 3) ** (1 / 3)
                packet_loss_events.append({'time': t, 'event': 'Packet Loss'})
            else:
                if self.cwnd < self.ssthresh or self.cwnd < low_window_threshold:
                    state = 'Slow Start'
                    self.cwnd += 1
                else:
                    state = 'Congestion Avoidance'
                    t_from_K = (t - bic_K) / self.rto
                    self.cwnd += t_from_K ** 3

            self.record_state_transition(state_transitions, t, state, self.cwnd, self.ssthresh, event)

            current_rtt = self.rtt + random.uniform(-5, 5)
            rtt_variations.append({'time': t, 'rtt': current_rtt})
            throughput = self.cwnd / current_rtt
            queue_length = self.simulate_queue_length_variation()
            acks = self.simulate_acknowledgments()

            queue_lengths.append(queue_length)
            acks_list.append(acks)

            simulation_results.append({'time': t, 'cwnd': self.cwnd, 'rtt': current_rtt,
                                       'throughput': throughput, 'state': state,
                                       'queue_length': queue_length, 'acks': acks})

        return simulation_results, packet_loss_events, rtt_variations, state_transitions, queue_lengths, acks_list

# Add more algorithms as needed.
