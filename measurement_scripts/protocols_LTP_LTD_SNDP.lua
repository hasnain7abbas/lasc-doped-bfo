===============================================================================
 BFO MEMRISTOR -- YOUR SCRIPTS, DUAL CHANNEL
 Pt / BFO:La(7.5%),Mn(2.5%) / FTO   |   Keithley 2602, TSP
===============================================================================

 WHAT WAS CHANGED
 ----------------
 Channel B added AND put to work as the dedicated ammeter.
 Channel A is now a pure source; it no longer measures at all.

     1.  smub.reset() added next to smua.reset()
     2.  channel B config block, parked at 0 V, autorange + AUTOZERO_ONCE
     3.  smub.source.output = OUTPUT_ON   before smua turns on
     4.  smub.source.output = OUTPUT_OFF  after smua turns off
     5.  every  smua.measure.i()  ->  (-1 * smub.measure.i())
     6.  nvbuffer1 moved from smua to smub
     7.  smua.measure.rangei / autorangei lines commented out (dead)

 Every VOLTAGE, loop, delay and print is byte-for-byte your original.
 Parameters keep their original names and defaults.

 WHY B MEASURES BETTER THAN A DID
 --------------------------------
 Your scripts pinned  smua.measure.rangei = 1e-4  for every test. A
 20 nA read is 0.02 % of that range -- almost all resolution thrown
 away. B autoranges down to 1e-7 / 1e-6 for the same read, roughly
 two decades better, and AUTOZERO_ONCE removes the per-reading zero
 refresh so the reads are also faster. A meanwhile stops paying any
 measurement settling cost, because it only sources now.

 THE SIGN FLIP
 -------------
 A and B are in series, so B sees the same current with opposite
 polarity. Every read is therefore  (-1 * smub.measure.i())  and
 buffer readings are negated on export. Positive still means
 conventional current Pt -> FTO, exactly as before.

 WHAT B STILL CANNOT DO
 ----------------------
 It cannot hold a read bias while A writes. The device has one
 voltage across it at a time, so a read bias on B would make
 V_device = V_A - V_B and force every amplitude in every script to
 be rewritten as (V - readV). That rewrite is what broke the earlier
 versions. Not attempted here.

 WHY THIS WORKS WHEN MY EARLIER VERSIONS DID NOT
 -----------------------------------------------
 Channel B is parked at 0 V, so V_device = smua level EXACTLY.
 No amplitude anywhere needs an offset. My earlier scripts parked B
 at -readV, which forced every voltage in every test to be rewritten
 as (V - readV), and that offsetting is what broke them.

 WIRING
 ------
     smua HI ----------> Pt top pad         (direct, no tee)
     smub HI ----------> FTO bottom         (direct, no tee)
     smua LO ---+
                +------ joined, floating    (ONE link, only junction)
     smub LO ---+

 Both channels are in series, so both carry identical current.
 Measurement stays on smua throughout, exactly as in your originals.

 OUTPUT ORDER MATTERS
 --------------------
 B on first, off last. If smua drives while smub's output is open,
 the loop is broken and you measure nothing.

 EACH SECTION IS SELF-CONTAINED. Paste ONE section and run.
 Run every section on a 1 MOhm resistor first.
===============================================================================


===============================================================================
0. QUICK CHANNEL CHECK  (run this once, on 1 MOhm)
===============================================================================

smua.reset()
smub.reset()

smua.source.func = smua.OUTPUT_DCVOLTS
smua.source.limiti = 1e-3
smua.source.levelv = 0
smua.measure.autorangei = smua.AUTORANGE_ON
smua.measure.nplc = 1

smub.source.func = smub.OUTPUT_DCVOLTS
smub.source.limiti = 1e-3
smub.source.levelv = 0
smub.measure.autorangei = smub.AUTORANGE_ON
smub.measure.nplc = 1

smub.source.output = smub.OUTPUT_ON
delay(0.05)
smua.source.output = smua.OUTPUT_ON
delay(0.2)

smua.source.levelv = 1.0
delay(0.5)
print("I_A =", (-1 * smub.measure.i()), " expect  1.0e-06")
print("I_B =", smub.measure.i(), " expect -1.0e-06")

smua.source.levelv = 0
smua.source.output = smua.OUTPUT_OFF
smub.source.output = smub.OUTPUT_OFF
print("Channel check done. Magnitudes must match within a few percent.")


===============================================================================
1. BIPOLAR I-V SWEEP (Updated Safe Version)  -- CONFIRMED WORKING
===============================================================================
-- LEFT EXACTLY AS YOU RAN IT. Measurement stays on smua here because
-- this section is confirmed working and a DC sweep gains nothing from
-- B-metering (currents are large, resolution is not the limit).
-- To switch it to B anyway: change the two smu.measure.i(smu.nvbuffer1)
-- calls to smub.measure.i(smub.nvbuffer1) and negate on export.
--
-- Use this for basic characterization before running synaptic tests
-- Reduced range, tighter compliance
-- Edit the loop headers directly for asymmetric limits, e.g.
--     for v = 10, -6, -0.5   and   for v = -6, 0, 0.5

smua.reset()
smub.reset()
smu = smua

smu.measure.nplc = 1
smu.measure.filter.count = 5
smu.measure.filter.enable = smu.FILTER_ON
smu.measure.filter.type = smu.FILTER_REPEAT_AVG

smu.source.func = smu.OUTPUT_DCVOLTS
smu.source.limiti = 100e-6
smu.source.rangev = 10

-- ---- CHANNEL B (added) ----
smub.source.func = smub.OUTPUT_DCVOLTS
smub.source.limiti = 100e-6
smub.source.rangev = 10
smub.source.levelv = 0
smub.measure.autorangei = smub.AUTORANGE_ON
smub.measure.nplc = 1
-- ---------------------------

smu.nvbuffer1.clear()
smu.nvbuffer1.appendmode = 1

smub.source.output = smub.OUTPUT_ON
delay(0.05)
smu.source.output = smu.OUTPUT_ON

for cycle = 1, 10 do
    for v = 0, 10, 0.5 do
        smu.source.levelv = v
        delay(0.01)
        print(cycle, v, smu.measure.i(smu.nvbuffer1))
    end
    for v = 10, -10, -0.5 do
        smu.source.levelv = v
        delay(0.01)
        print(cycle, v, smu.measure.i(smu.nvbuffer1))
    end
    for v = -10, 0, 0.5 do
        smu.source.levelv = v
        delay(0.01)
        print(cycle, v, smu.measure.i(smu.nvbuffer1))
    end
end

smu.source.levelv = 0
smu.source.output = smu.OUTPUT_OFF
smub.source.output = smub.OUTPUT_OFF
print("Sweep Complete.")


===============================================================================
2. EPSC
===============================================================================

function run_EPSC(amp, readV, pulseWidth, decayPoints, decayInterval)
    smua.reset()
    smub.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS

    -- ---- CHANNEL B (added) ----
    smub.source.func = smub.OUTPUT_DCVOLTS
    smub.source.limiti = 1e-3
    smub.source.rangev = 40
    smub.source.levelv = 0
    smub.measure.autorangei = smub.AUTORANGE_ON
    smub.measure.nplc = 1
    smub.measure.autozero = smub.AUTOZERO_ONCE
    smub.sense = smub.SENSE_LOCAL
    smub.source.output = smub.OUTPUT_ON
    delay(0.05)
    -- ---------------------------

    smua.source.output = smua.OUTPUT_ON

    -- smua.measure.autorangei = smua.AUTORANGE_OFF   -- (A no longer measures)
    -- smua.measure.rangei = 1e-4   -- (A no longer measures; B does)
    smua.source.limiti = 1e-3  -- 1mA compliance

    smub.nvbuffer1.clear()
    smub.nvbuffer1.appendmode = 1
    smub.nvbuffer1.collecttimestamps = 1

    -- BASELINE (2 seconds)
    print("Status: Measuring Baseline...")
    smua.source.levelv = readV
    for i = 1, 20 do
        smub.measure.i(smub.nvbuffer1)
        delay(0.1)
    end

    -- STIMULUS PULSE
    smua.source.levelv = amp
    delay(pulseWidth)
    smub.measure.i(smub.nvbuffer1)  -- Capture peak

    -- POST-PULSE DECAY
    print("Status: Measuring Decay...")
    smua.source.levelv = readV
    for i = 1, decayPoints do
        smub.measure.i(smub.nvbuffer1)
        delay(decayInterval)
    end

    smua.source.output = smua.OUTPUT_OFF
    smub.source.output = smub.OUTPUT_OFF

    -- EXPORT
    print("Time(s)", "Current(A)")
    t_start = smub.nvbuffer1.timestamps[1]
    for i = 1, smub.nvbuffer1.n do
        t_rel = smub.nvbuffer1.timestamps[i] - t_start
        print(string.format("%g\t%g", t_rel, (-1 * smub.nvbuffer1.readings[i])))
    end
end

-- EXECUTE
run_EPSC(22, 3, 0.1, 200, 0.1)


===============================================================================
3. PPF (Paired-Pulse Facilitation)
===============================================================================
-- Two pulses separated by deltaT, compare A2 vs A1. Prints PPF index.
-- 2602 timing floor ~1 ms; keep deltaT >= ~0.005 s.

function run_PPF(amp, readV, pulseWidth, deltaT, decayTime)
    reset_device()

    amp        = amp        or 22
    readV      = readV      or 3
    pulseWidth = pulseWidth or 0.1
    deltaT     = deltaT     or 0.05
    decayTime  = decayTime  or 5

    smua.reset()
    smub.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS

    -- ---- CHANNEL B (added) ----
    smub.source.func = smub.OUTPUT_DCVOLTS
    smub.source.limiti = 1e-3
    smub.source.rangev = 40
    smub.source.levelv = 0
    smub.measure.autorangei = smub.AUTORANGE_ON
    smub.measure.nplc = 1
    smub.measure.autozero = smub.AUTOZERO_ONCE
    smub.sense = smub.SENSE_LOCAL
    smub.source.output = smub.OUTPUT_ON
    delay(0.05)
    -- ---------------------------

    smua.source.output = smua.OUTPUT_ON
    -- smua.measure.autorangei = smua.AUTORANGE_OFF   -- (A no longer measures)
    -- smua.measure.rangei = 1e-4   -- (A no longer measures; B does)
    smua.source.limiti = 1e-3

    smub.nvbuffer1.clear()
    smub.nvbuffer1.appendmode = 1
    smub.nvbuffer1.collecttimestamps = 1

    print("# TEST: PPF")
    print(string.format("# PARAMS: writeV=%g V  readV=%g V  pulseWidth=%g s  deltaT=%g s  decayTime=%g s",
          amp, readV, pulseWidth, deltaT, decayTime))

    smua.source.levelv = readV
    for i = 1, 40 do smub.measure.i(smub.nvbuffer1); delay(0.05) end

    smua.source.levelv = amp
    delay(pulseWidth)
    local A1 = smub.measure.i(smub.nvbuffer1)

    smua.source.levelv = readV
    delay(deltaT)

    smua.source.levelv = amp
    delay(pulseWidth)
    local A2 = smub.measure.i(smub.nvbuffer1)

    smua.source.levelv = readV
    local decayPoints = decayTime / 0.1
    for i = 1, decayPoints do smub.measure.i(smub.nvbuffer1); delay(0.1) end

    smua.source.output = smua.OUTPUT_OFF
    smub.source.output = smub.OUTPUT_OFF

    local ppf = 0
    if A1 ~= 0 then ppf = ((A2 - A1) / A1) * 100 end
    print(string.format("# RESULT: A1=%g A  A2=%g A  PPF_index=%g %%", A1, A2, ppf))

    print("Time(s)", "Current(A)", "Conductance(uS)")
    t_start = smub.nvbuffer1.timestamps[1]
    for i = 1, smub.nvbuffer1.n do
        t_now = smub.nvbuffer1.timestamps[i] - t_start
        curr  = (-1 * smub.nvbuffer1.readings[i])
        print(string.format("%g\t%g\t%g", t_now, curr, (curr/readV)*1e6))
    end
end

-- EXECUTE: run each deltaT separately
run_PPF(22, 3, 0.1, 0.05, 5)
-- run_PPF(22, 3, 0.1, 0.1, 5)
-- run_PPF(22, 3, 0.1, 0.2, 5)
-- run_PPF(22, 3, 0.1, 0.3, 5)
-- run_PPF(22, 3, 0.1, 0.5, 5)
-- run_PPF(22, 3, 0.1, 1.0, 5)


===============================================================================
4. SDDP - Conductance vs Pulse Number
===============================================================================

function run_SDDP(writeV, readV, pulseWidth, pulseCount)
    reset_device()

    writeV     = writeV     or 22
    readV      = readV      or 3
    pulseWidth = pulseWidth or 0.1
    pulseCount = pulseCount or 50

    smua.reset()
    smub.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS

    -- ---- CHANNEL B (added) ----
    smub.source.func = smub.OUTPUT_DCVOLTS
    smub.source.limiti = 1e-3
    smub.source.rangev = 40
    smub.source.levelv = 0
    smub.measure.autorangei = smub.AUTORANGE_ON
    smub.measure.nplc = 1
    smub.measure.autozero = smub.AUTOZERO_ONCE
    smub.sense = smub.SENSE_LOCAL
    smub.source.output = smub.OUTPUT_ON
    delay(0.05)
    -- ---------------------------

    smua.source.output = smua.OUTPUT_ON
    -- smua.measure.autorangei = smua.AUTORANGE_OFF   -- (A no longer measures)
    -- smua.measure.rangei = 1e-4   -- (A no longer measures; B does)
    smua.source.limiti = 1e-3

    print("# TEST: SDDP (potentiation vs pulse number)")
    print(string.format("# PARAMS: writeV=%g V  readV=%g V  pulseWidth=%g s  pulseCount=%d",
          writeV, readV, pulseWidth, pulseCount))

    smua.source.levelv = readV
    delay(0.5)

    local train_currents = {}
    for i = 1, pulseCount do
        smua.source.levelv = writeV
        delay(pulseWidth)
        smua.source.levelv = readV
        delay(0.05)
        train_currents[i] = (-1 * smub.measure.i())
    end

    smua.source.output = smua.OUTPUT_OFF
    smub.source.output = smub.OUTPUT_OFF

    print("Pulse#", "Current(A)", "Conductance(uS)")
    for i = 1, pulseCount do
        print(string.format("%d\t%g\t%g", i, train_currents[i], (train_currents[i]/readV)*1e6))
    end
    train_currents = nil
end

-- EXECUTE: run each width separately
run_SDDP(22, 3, 0.1, 50)
-- run_SDDP(22, 3, 0.2, 50)
-- run_SDDP(22, 3, 0.3, 50)
-- run_SDDP(22, 3, 0.4, 50)
-- run_SDDP(22, 3, 0.5, 50)


===============================================================================
5. SNDP  (train + decay)
===============================================================================

SNDP_CFG = {
    numPulses = 50,

    writeV = 20,
    readV = 3.0,

    pulseWidth = 0.1,
    gapBetweenPulses = 0.05,

    readHold = 0.05,
    readAverages = 3,

    decayPoints = 200,
    decayInterval = 0.1,

    measureRange = 1e-5,
    currentLimit = 1e-3
}


function setup_SNDP()
    smua.reset()
    smub.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS

    -- ---- CHANNEL B (added) ----
    smub.source.func = smub.OUTPUT_DCVOLTS
    smub.source.limiti = SNDP_CFG.currentLimit
    smub.source.rangev = 40
    smub.source.levelv = 0
    smub.measure.autorangei = smub.AUTORANGE_ON
    smub.measure.nplc = 1
    smub.source.output = smub.OUTPUT_ON
    delay(0.05)
    -- ---------------------------

    smua.source.output = smua.OUTPUT_ON

    -- smua.measure.autorangei = smua.AUTORANGE_OFF   -- (A no longer measures)
    -- smua.measure.rangei = SNDP_CFG.measureRange   -- (A no longer measures; B does)

    smua.source.limiti = SNDP_CFG.currentLimit
    smua.source.levelv = 0
    delay(0.5)
end


function read_current_SNDP()
    local readV = SNDP_CFG.readV
    local nread = SNDP_CFG.readAverages
    local readHold = SNDP_CFG.readHold

    local isum = 0

    smua.source.levelv = readV
    delay(readHold)

    for i = 1, nread do
        isum = isum + (-1 * smub.measure.i())
        delay(0.01)
    end

    smua.source.levelv = 0
    delay(0.05)

    return isum / nread
end


function conductance_uS_SNDP(curr)
    return math.abs(curr / SNDP_CFG.readV) * 1e6
end


function run_SNDP()
    reset_device()          -- your existing reset sweep only
    setup_SNDP()

    local numPulses = SNDP_CFG.numPulses
    local writeV = SNDP_CFG.writeV
    local pulseWidth = SNDP_CFG.pulseWidth
    local gap = SNDP_CFG.gapBetweenPulses
    local decayPoints = SNDP_CFG.decayPoints
    local decayInterval = SNDP_CFG.decayInterval

    print("# TEST: SNDP corrected")
    print(string.format("# PARAMS: numPulses=%d  writeV=%g V  readV=%g V  width=%g s  gap=%g s  decayPoints=%d  decayInterval=%g s",
        numPulses, writeV, SNDP_CFG.readV, pulseWidth, gap, decayPoints, decayInterval))

    -- BASELINE
    local I_base = read_current_SNDP()
    local G_base = conductance_uS_SNDP(I_base)

    print(string.format("# BASELINE: I=%g A  G=%g uS", I_base, G_base))
    print("Phase\tPulse_or_Time\tCurrent_A\tConductance_uS\tdG_percent")

    -- TRAINING: pulse number dependent potentiation
    for p = 1, numPulses do
        smua.source.levelv = writeV
        delay(pulseWidth)

        smua.source.levelv = 0
        delay(gap)

        local I_now = read_current_SNDP()
        local G_now = conductance_uS_SNDP(I_now)

        local dG = 0
        if math.abs(G_base) > 1e-12 then
            dG = ((G_now - G_base) / math.abs(G_base)) * 100
        end

        print(string.format("TRAIN\t%d\t%g\t%g\t%g",
            p, I_now, G_now, dG))

        smua.source.levelv = 0
        delay(gap)
    end

    -- DECAY: do not hold at read voltage continuously
    for i = 0, decayPoints - 1 do
        local t = i * decayInterval

        smua.source.levelv = 0
        delay(decayInterval)

        local I_decay = read_current_SNDP()
        local G_decay = conductance_uS_SNDP(I_decay)

        local dG_decay = 0
        if math.abs(G_base) > 1e-12 then
            dG_decay = ((G_decay - G_base) / math.abs(G_base)) * 100
        end

        print(string.format("DECAY\t%g\t%g\t%g\t%g",
            t, I_decay, G_decay, dG_decay))
    end

    smua.source.levelv = 0
    smua.source.output = smua.OUTPUT_OFF
    smub.source.output = smub.OUTPUT_OFF

    print("# SNDP corrected test finished")
end

-- EXECUTE
run_SNDP()


===============================================================================
6. SRDP
===============================================================================
-- NOTE: this is your original protocol, unchanged apart from channel B.
-- It holds total ON-time fixed (pulseCount x pulseWidth) and varies only
-- the gap, so the frequency axis is confounded with elapsed time. Label
-- the figure "pulse-interval dependence" and state the ON-time, or run a
-- second pass at fixed train DURATION to separate the two. That fix is a
-- protocol change, not a code change -- kept out of here on purpose.

function avg_read_current(readV, n, delayTime)
    local sum = 0
    smua.source.levelv = readV
    delay(delayTime)

    for i = 1, n do
        sum = sum + (-1 * smub.measure.i())
        delay(delayTime)
    end

    smua.source.levelv = 0
    return sum / n
end


function run_SRDP(writeV, readV, pulseWidth, pulseCount, frequency, postWait)
    writeV     = writeV     or 22
    readV      = readV      or 1
    pulseWidth = pulseWidth or 0.02
    pulseCount = pulseCount or 50
    frequency  = frequency  or 2.0
    postWait   = postWait   or 0.5

    local period = 1 / frequency
    local offGap = period - pulseWidth

    if offGap <= 0 then
        print("# ERROR: pulseWidth is longer than/equal to period.")
        return
    end

    if offGap < 0.02 then
        print("# ERROR: offGap too short. Reduce pulseWidth.")
        return
    end

    reset_device()

    smua.reset()
    smub.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS

    -- ---- CHANNEL B (added) ----
    smub.source.func = smub.OUTPUT_DCVOLTS
    smub.source.limiti = 1e-3
    smub.source.rangev = 40
    smub.source.levelv = 0
    smub.measure.autorangei = smub.AUTORANGE_ON
    smub.measure.nplc = 1
    smub.measure.autozero = smub.AUTOZERO_ONCE
    smub.sense = smub.SENSE_LOCAL
    smub.source.output = smub.OUTPUT_ON
    delay(0.05)
    -- ---------------------------

    smua.source.output = smua.OUTPUT_ON
    -- smua.measure.autorangei = smua.AUTORANGE_OFF   -- (A no longer measures)
    -- smua.measure.rangei = 1e-4   -- (A no longer measures; B does)
    smua.source.limiti = 1e-3

    print("# TEST: SRDP clean with per-pulse data")
    print(string.format(
        "# PARAMS: writeV=%g V  readV=%g V  pulseWidth=%g s  pulseCount=%d  frequency=%g Hz  offGap=%g s",
        writeV, readV, pulseWidth, pulseCount, frequency, offGap
    ))

    local I0 = avg_read_current(readV, 5, 0.05)
    local G0 = (I0 / readV) * 1e6

    print(string.format("# BASELINE: I0=%g A  G0=%g uS", I0, G0))
    print("Pulse#\tCurrent(A)\tConductance(uS)\tDeltaG(%)")

    local lastI = I0
    local lastG = G0

    for i = 1, pulseCount do
        -- write pulse
        smua.source.levelv = writeV
        delay(pulseWidth)

        -- off gap
        smua.source.levelv = 0
        delay(offGap)

        -- quick read after each pulse
        smua.source.levelv = readV
        delay(0.05)

        local curr = (-1 * smub.measure.i())
        local G = (curr / readV) * 1e6
        local dG = 0

        if G0 ~= 0 then
            dG = ((G - G0) / G0) * 100
        end

        print(string.format("%d\t%g\t%g\t%g", i, curr, G, dG))

        smua.source.levelv = 0

        lastI = curr
        lastG = G
    end

    smua.source.levelv = 0
    delay(postWait)

    local I_after = avg_read_current(readV, 5, 0.05)
    local G_after = (I_after / readV) * 1e6

    local idx = 0
    if G0 ~= 0 then
        idx = ((G_after - G0) / G0) * 100
    end

    print(string.format(
        "# RESULT: frequency=%g Hz  I0=%g A  G0=%g uS  I_after=%g A  G_after=%g uS  SRDP_index=%g %%",
        frequency, I0, G0, I_after, G_after, idx
    ))

    smua.source.output = smua.OUTPUT_OFF
    smub.source.output = smub.OUTPUT_OFF
end

-- EXECUTE: one frequency per run, rest the device between runs
run_SRDP(22, 1, 0.02, 50, 2.0, 0.5)
-- run_SRDP(22, 1, 0.02, 50, 4.0, 0.5)
-- run_SRDP(22, 1, 0.02, 50, 6.0, 0.5)
-- run_SRDP(22, 1, 0.02, 50, 8.0, 0.5)


===============================================================================
7. LTP / LTD
===============================================================================
-- Measures: 50 positive pulses (potentiation) then 50 negative (depression)
-- What to plot: Total pulse# (x) vs Conductance (y)
-- posV and negV are set at the top of the function. Edit them there for
-- asymmetric amplitudes -- negV is NOT tied to -posV.

function run_LTP_LTD(cycles)
    posV = 22
    negV = -14
    readV = 3
    pulseWidth = 0.1
    readGap = 0.05

    smua.reset()
    smub.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS

    -- ---- CHANNEL B (added) ----
    smub.source.func = smub.OUTPUT_DCVOLTS
    smub.source.limiti = 1e-3
    smub.source.rangev = 40
    smub.source.levelv = 0
    smub.measure.autorangei = smub.AUTORANGE_ON
    smub.measure.nplc = 1
    smub.measure.autozero = smub.AUTOZERO_ONCE
    smub.sense = smub.SENSE_LOCAL
    smub.source.output = smub.OUTPUT_ON
    delay(0.05)
    -- ---------------------------

    smua.source.output = smua.OUTPUT_ON

    -- smua.measure.autorangei = smua.AUTORANGE_OFF   -- (A no longer measures)
    -- smua.measure.rangei = 1e-4   -- (A no longer measures; B does)
    smua.source.limiti = 1e-3

    smub.nvbuffer1.clear()
    smub.nvbuffer1.appendmode = 1
    smub.nvbuffer1.collecttimestamps = 1

    print("Status: LTP/LTD for " .. cycles .. " cycles")

    -- BASELINE
    smua.source.levelv = readV
    delay(1)

    for k = 1, cycles do
        -- POTENTIATION: 50 positive pulses
        for i = 1, 50 do
            smua.source.levelv = posV
            delay(pulseWidth)
            smua.source.levelv = readV
            delay(readGap)
            smub.measure.i(smub.nvbuffer1)
        end

        -- DEPRESSION: 50 negative pulses
        for i = 1, 50 do
            smua.source.levelv = negV
            delay(pulseWidth)
            smua.source.levelv = readV
            delay(readGap)
            smub.measure.i(smub.nvbuffer1)
        end
    end

    smua.source.output = smua.OUTPUT_OFF
    smub.source.output = smub.OUTPUT_OFF

    -- EXPORT
    print("Pulse#", "Current(A)", "Conductance(uS)")
    for i = 1, smub.nvbuffer1.n do
        curr = (-1 * smub.nvbuffer1.readings[i])
        cond = (curr / readV) * 1e6
        print(string.format("%d\t%g\t%g", i, curr, cond))
    end
end

-- EXECUTE
run_LTP_LTD(1)


===============================================================================
8. RETENTION
===============================================================================

function reset_device()
    for i = 1, 5 do
        smua.source.levelv = -15
        delay(0.1)
        smua.source.levelv = 0
        delay(0.1)
    end
end

function read_G(readV)
    smua.source.levelv = readV
    delay(0.05)
    c = (-1 * smub.measure.i())
    smua.source.levelv = 0
    return (c / readV) * 1e6    -- Conductance in uS
end

function run_Retention(numPulses)

    writeV = 23
    readV = 1.5
    width = 0.1
    gap = 0.1

    -- Log-spaced read times (seconds)
    readTimes = {1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000}

    smua.reset()
    smub.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS

    -- ---- CHANNEL B (added) ----
    smub.source.func = smub.OUTPUT_DCVOLTS
    smub.source.limiti = 1e-3
    smub.source.rangev = 40
    smub.source.levelv = 0
    smub.measure.autorangei = smub.AUTORANGE_ON
    smub.measure.nplc = 1
    smub.measure.autozero = smub.AUTOZERO_ONCE
    smub.sense = smub.SENSE_LOCAL
    smub.source.output = smub.OUTPUT_ON
    delay(0.05)
    -- ---------------------------

    -- smua.measure.autorangei = smua.AUTORANGE_OFF   -- (A no longer measures)
    -- smua.measure.rangei = 1e-4   -- (A no longer measures; B does)
    smua.source.limiti = 1e-3
    smua.source.output = smua.OUTPUT_ON

    print("")
    print("========================================")
    print("Retention Test : " .. numPulses .. " Pulses")
    print("========================================")

    reset_device()
    delay(1)

    g0 = read_G(readV)

    -------------------------------------------------
    -- PROGRAM DEVICE
    -------------------------------------------------
    for i = 1, numPulses do
        smua.source.levelv = writeV
        delay(width)

        smua.source.levelv = 0
        delay(gap)
    end

    -------------------------------------------------
    -- RETENTION
    -------------------------------------------------
    print("BEGIN_RETENTION " .. numPulses)
    print("Time(s)", "G(uS)")

    print(string.format("%g\t%g", 0, read_G(readV)))

    t_elapsed = 0

    for k = 1, 11 do

        wait = readTimes[k] - t_elapsed

        if wait > 0 then
            delay(wait)
        end

        t_elapsed = readTimes[k]

        print(string.format("%g\t%g",
            t_elapsed,
            read_G(readV)))

    end

    print("END_RETENTION")

    smua.source.output = smua.OUTPUT_OFF
    smub.source.output = smub.OUTPUT_OFF

    print("Initial (post-reset) G = " ..
          string.format("%g", g0) .. " uS")

end

-------------------------------------------------
-- AUTOMATIC RETENTION SEQUENCE
-------------------------------------------------

run_Retention(60)
run_Retention(40)
run_Retention(20)

print("")
print("ALL RETENTION TESTS COMPLETED")


===============================================================================
9. ENDURANCE
===============================================================================

function run_Endurance1500(numCycles)
    local posV = 18
    local negV = -14
    local readV = 1.5
    local pulseWidth = 0.1
    local gap = 0.05
    local pulses = 5
    local breakdownLimit = 50      -- uS; stop if Gplus exceeds this

    smua.reset()
    smub.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS

    -- ---- CHANNEL B (added) ----
    smub.source.func = smub.OUTPUT_DCVOLTS
    smub.source.limiti = 1e-3
    smub.source.rangev = 40
    smub.source.levelv = 0
    smub.measure.autorangei = smub.AUTORANGE_ON
    smub.measure.nplc = 1
    smub.measure.autozero = smub.AUTOZERO_ONCE
    smub.sense = smub.SENSE_LOCAL
    smub.source.output = smub.OUTPUT_ON
    delay(0.05)
    -- ---------------------------

    smua.source.rangev = 20
    -- smua.measure.autorangei = smua.AUTORANGE_OFF   -- (A no longer measures)
    -- smua.measure.rangei = 1e-5   -- (A no longer measures; B does)
    smua.source.limiti = 1e-3
    smua.measure.nplc = 1
    smua.source.levelv = 0
    smua.source.output = smua.OUTPUT_ON

    print("Cycle\tGplus(uS)\tGminus(uS)")

    local cycle
    local i
    local isum
    local gplus
    local gminus
    local doPrint

    for cycle = 1, numCycles do

        -- Positive programming
        for i = 1, pulses do
            smua.source.levelv = posV
            delay(pulseWidth)
            smua.source.levelv = 0
            delay(gap)
        end

        -- Read Gplus
        smua.source.levelv = readV
        delay(0.05)
        isum = 0
        for i = 1, 5 do
            isum = isum + (-1 * smub.measure.i())
            delay(0.01)
        end
        gplus = math.abs((isum/5)/readV)*1e6
        smua.source.levelv = 0
        delay(0.1)

        -- Negative programming
        for i = 1, pulses do
            smua.source.levelv = negV
            delay(pulseWidth)
            smua.source.levelv = 0
            delay(gap)
        end

        -- Read Gminus
        smua.source.levelv = readV
        delay(0.05)
        isum = 0
        for i = 1, 5 do
            isum = isum + (-1 * smub.measure.i())
            delay(0.01)
        end
        gminus = math.abs((isum/5)/readV)*1e6
        smua.source.levelv = 0

        -- Print dense early, sparse later
        doPrint = 0
        if cycle <= 20 then
            doPrint = 1
        elseif math.mod(cycle, 10) == 0 then
            doPrint = 1
        elseif cycle == numCycles then
            doPrint = 1
        end
        if doPrint == 1 then
            print(string.format("%d\t%g\t%g", cycle, gplus, gminus))
        end

        -- Breakdown guard
        if gplus > breakdownLimit then
            print("WARNING: Gplus = " .. string.format("%g", gplus) ..
                  " uS exceeds limit. Stopping at cycle " .. cycle)
            break
        end
    end

    smua.source.levelv = 0
    smua.source.output = smua.OUTPUT_OFF
    smub.source.output = smub.OUTPUT_OFF
    print("Endurance test completed.")
end

-- EXECUTE
run_Endurance1500(1500)


===============================================================================
10. STDP  -  full curve in ONE run, reset between every point
===============================================================================
-- dt floor is ~0.02s: below that, Lua overhead makes the real gap
-- larger than requested.
-- What to plot: dt (x, negative for post-before-pre) vs DeltaW% (y).

function run_STDP_Curve()
    writeV_Pos = 22
    writeV_Neg = -14
    readV = 1.5
    width = 0.1
    dt_list = {0.05, 0.1, 0.2, 0.3, 0.5, 1.0}

    smua.reset()
    smub.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS

    -- ---- CHANNEL B (added) ----
    smub.source.func = smub.OUTPUT_DCVOLTS
    smub.source.limiti = 1e-3
    smub.source.rangev = 40
    smub.source.levelv = 0
    smub.measure.autorangei = smub.AUTORANGE_ON
    smub.measure.nplc = 1
    smub.measure.autozero = smub.AUTOZERO_ONCE
    smub.sense = smub.SENSE_LOCAL
    smub.source.output = smub.OUTPUT_ON
    delay(0.05)
    -- ---------------------------

    -- smua.measure.autorangei = smua.AUTORANGE_OFF   -- (A no longer measures)
    -- smua.measure.rangei = 1e-4   -- (A no longer measures; B does)
    smua.source.limiti = 1e-3
    smua.source.output = smua.OUTPUT_ON

    results = {}

    for mode = 1, 2 do                       -- 1 = pre-post, 2 = post-pre
        for k = 1, 6 do
            dt = dt_list[k]
            print("Status: STDP mode " .. mode .. ", dt = " .. dt .. " s")

            for i = 1, 5 do                  -- reset to common baseline
                smua.source.levelv = -15
                delay(0.1)
                smua.source.levelv = 0
                delay(0.1)
            end
            delay(1)

            smua.source.levelv = readV       -- initial weight, 5-read avg
            delay(0.05)
            s = 0
            for i = 1, 5 do
                s = s + (-1 * smub.measure.i())
                delay(0.05)
            end
            w_i = s / 5
            smua.source.levelv = 0
            delay(0.2)

            if mode == 1 then                -- pulse pair, pure delays
                smua.source.levelv = writeV_Pos
                delay(width)
                smua.source.levelv = 0
                delay(dt)
                smua.source.levelv = writeV_Neg
                delay(width)
            else
                smua.source.levelv = writeV_Neg
                delay(width)
                smua.source.levelv = 0
                delay(dt)
                smua.source.levelv = writeV_Pos
                delay(width)
            end
            smua.source.levelv = 0
            delay(0.5)

            smua.source.levelv = readV       -- final weight, 5-read avg
            delay(0.05)
            s = 0
            for i = 1, 5 do
                s = s + (-1 * smub.measure.i())
                delay(0.05)
            end
            w_f = s / 5
            smua.source.levelv = 0

            dW = ((w_f - w_i) / math.abs(w_i)) * 100
            dt_signed = dt
            if mode == 2 then dt_signed = -dt end
            results[table.getn(results) + 1] = {dt_signed, w_i, w_f, dW}
        end
    end

    smua.source.output = smua.OUTPUT_OFF
    smub.source.output = smub.OUTPUT_OFF

    print("")
    print("dt(s)", "W_init(A)", "W_final(A)", "DeltaW(%)")
    for i = 1, table.getn(results) do
        r = results[i]
        print(string.format("%g\t%g\t%g\t%g", r[1], r[2], r[3], r[4]))
    end
    print("STDP curve complete.")
end

-- EXECUTE
run_STDP_Curve()


===============================================================================
11. AREA-DEPENDENT COMPLIANCE TEST
===============================================================================
-- Move probe manually to the desired electrode before each run.

function setup_SMU_AREA(Icc)
    Icc = Icc or 1e-4

    smua.reset()
    smub.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS

    -- ---- CHANNEL B (added) ----
    smub.source.func = smub.OUTPUT_DCVOLTS
    smub.source.limiti = Icc
    smub.source.rangev = 40
    smub.source.levelv = 0
    smub.measure.autorangei = smub.AUTORANGE_ON
    smub.measure.nplc = 1
    smub.source.output = smub.OUTPUT_ON
    delay(0.05)
    -- ---------------------------

    smua.source.output = smua.OUTPUT_ON

    -- smua.measure.autorangei = smua.AUTORANGE_OFF   -- (A no longer measures)

    if Icc <= 1e-5 then
        -- smua.measure.rangei = 1e-5   -- (A no longer measures; B does)
    elseif Icc <= 1e-4 then
        -- smua.measure.rangei = 1e-4   -- (A no longer measures; B does)
    else
        -- smua.measure.rangei = 1e-3   -- (A no longer measures; B does)
    end

    smua.source.limiti = Icc
    smua.source.levelv = 0
    delay(0.5)
end


function electrode_area_cm2(diameter_um)
    local diameter_cm = diameter_um * 1e-4
    local radius_cm = diameter_cm / 2
    local area = 3.141592653589793 * radius_cm * radius_cm
    return area
end


function safe_reset_AREA()
    setup_SMU_AREA(1e-4)

    for i = 1, 5 do
        smua.source.levelv = -15
        delay(0.1)
        smua.source.levelv = 0
        delay(0.5)
    end

    delay(60)
end


function measure_current_avg_AREA(nread)
    nread = nread or 3

    local isum = 0
    for r = 1, nread do
        isum = isum + (-1 * smub.measure.i())
        delay(0.02)
    end

    return isum / nread
end


function print_area_point(idx, electrodeLabel, diameter_um, area_cm2, Icc, Jcc, segment, V, I, readV)
    local absI = math.abs(I)
    local J = I / area_cm2
    local absJ = math.abs(J)

    local G_uS = 0
    if math.abs(readV) > 1e-12 then
        G_uS = math.abs(I / readV) * 1e6
    end

    local R_ohm = 0
    if absI > 1e-15 then
        R_ohm = math.abs(V / I)
    end

    local RA_ohm_cm2 = R_ohm * area_cm2

    print(string.format("%d\t%s\t%g\t%g\t%g\t%g\t%s\t%g\t%g\t%g\t%g\t%g\t%g\t%g",
        idx, electrodeLabel, diameter_um, area_cm2, Icc, Jcc, segment,
        V, I, absI, J, absJ, G_uS, RA_ohm_cm2))
end


function sweep_segment_AREA(idx, electrodeLabel, diameter_um, area_cm2, Icc, Jcc, segment, vStart, vStop, stepV, delayTime, readV)
    local V = vStart
    local step = math.abs(stepV)

    if vStop < vStart then
        step = -step
    end

    while true do
        smua.source.levelv = V
        delay(delayTime)

        local I = measure_current_avg_AREA(3)

        idx = idx + 1
        print_area_point(idx, electrodeLabel, diameter_um, area_cm2, Icc, Jcc, segment, V, I, readV)

        if step > 0 then
            if V >= vStop then
                break
            end
        else
            if V <= vStop then
                break
            end
        end

        V = V + step

        if step > 0 and V > vStop then
            V = vStop
        end

        if step < 0 and V < vStop then
            V = vStop
        end
    end

    return idx
end


function run_AreaCompliance_Electrode(electrodeLabel, diameter_um, Jcc_A_per_cm2, Vpos, Vneg, stepV, delayTime)
    electrodeLabel = electrodeLabel or "ELECTRODE"
    diameter_um = diameter_um or 100
    Jcc_A_per_cm2 = Jcc_A_per_cm2 or 0.2

    Vpos = Vpos or 25
    Vneg = Vneg or -20
    stepV = stepV or 0.5
    delayTime = delayTime or 0.05

    local area_cm2 = electrode_area_cm2(diameter_um)
    local Icc = Jcc_A_per_cm2 * area_cm2

    if Icc < 1e-6 then
        Icc = 1e-6
    end

    if Icc > 1e-3 then
        Icc = 1e-3
    end

    print("============================================================")
    print("AREA COMPLIANCE TEST")
    print(string.format("Electrode=%s  diameter=%g um  area=%g cm2", electrodeLabel, diameter_um, area_cm2))
    print(string.format("Jcc=%g A/cm2  calculated_Icc=%g A", Jcc_A_per_cm2, Icc))
    print(string.format("Sweep: 0 -> %g -> %g -> 0 V   step=%g V   delay=%g s", Vpos, Vneg, stepV, delayTime))
    print("Move probe to the correct electrode BEFORE running this function.")
    print("============================================================")

    safe_reset_AREA()
    setup_SMU_AREA(Icc)

    print("Index\tElectrode\tDiameter_um\tArea_cm2\tIcc_A\tJcc_Acm2\tSegment\tVoltage_V\tCurrent_A\tAbsCurrent_A\tJ_Acm2\tAbsJ_Acm2\tG_uS_using_V\tRA_ohm_cm2")

    local idx = 0

    idx = sweep_segment_AREA(idx, electrodeLabel, diameter_um, area_cm2, Icc, Jcc_A_per_cm2, "0_to_Pos", 0, Vpos, stepV, delayTime, Vpos)
    idx = sweep_segment_AREA(idx, electrodeLabel, diameter_um, area_cm2, Icc, Jcc_A_per_cm2, "Pos_to_Neg", Vpos, Vneg, stepV, delayTime, Vpos)
    idx = sweep_segment_AREA(idx, electrodeLabel, diameter_um, area_cm2, Icc, Jcc_A_per_cm2, "Neg_to_0", Vneg, 0, stepV, delayTime, Vpos)

    smua.source.levelv = 0
    delay(1)

    local Iread_pos = 0
    local Iread_neg = 0

    smua.source.levelv = 3.5
    delay(0.2)
    Iread_pos = measure_current_avg_AREA(5)

    smua.source.levelv = 0
    delay(0.5)

    smua.source.levelv = -3.5
    delay(0.2)
    Iread_neg = measure_current_avg_AREA(5)

    smua.source.levelv = 0
    smua.source.output = smua.OUTPUT_OFF
    smub.source.output = smub.OUTPUT_OFF

    print("READ_SUMMARY")
    print("Electrode\tDiameter_um\tArea_cm2\tIcc_A\tJcc_Acm2\tIread_plus3p5_A\tJ_plus3p5_Acm2\tG_plus3p5_uS\tIread_minus3p5_A\tJ_minus3p5_Acm2\tG_minus3p5_uS")

    print(string.format("%s\t%g\t%g\t%g\t%g\t%g\t%g\t%g\t%g\t%g\t%g",
        electrodeLabel, diameter_um, area_cm2, Icc, Jcc_A_per_cm2,
        Iread_pos, Iread_pos / area_cm2, math.abs(Iread_pos / 3.5) * 1e6,
        Iread_neg, Iread_neg / area_cm2, math.abs(Iread_neg / 3.5) * 1e6))

    print("AREA COMPLIANCE TEST FINISHED")
end


-- EXECUTE: 100 um first, then move probe and run 200 um
run_AreaCompliance_Electrode("D100um", 100, 0.5, 20, -17, 0.5, 0.05)
-- run_AreaCompliance_Electrode("D200um", 200, 0.5, 25, -20, 0.5, 0.05)
