===============================================================================
 SYNAPTIC TEST SUITE (FINAL, CORRECTED)  -  Keithley 2602
 LaMn-BFO (7.5/2.5) / FTO , Pt top (300 um) , film 350-400 nm
===============================================================================
 Sequence (Luo et al., Front. Neurosci. 16:1016026, 2022 - valid track):
   I-V SWEEP (first) -> EPSC -> PPF -> SDDP -> SDDP-decay -> SRDP -> STDP
   -> SNDP -> Multi-level -> P&D -> Retention -> Endurance

 WHAT WAS FIXED IN THIS VERSION
 ------------------------------
 1. I-V SWEEP moved to the TOP (Test 1), because you start with it. It also
    now finds your operating window before any pulse test.
 2. STDP BUG FIXED: dt is now written SIGNED (+dt for pre->post mode 1,
    -dt for post->pre mode 2). Before, both branches printed +dt and
    overlapped on the plot. (This was ChatGPT's correct catch.)
 3. P&D (LTP/LTD) FIXED: added a clean SINGLE-CYCLE mode and a RESET +
    relaxation wait BETWEEN the potentiation half and the depression half,
    so the depression block no longer inherits the potentiation state.
    Your old data oscillated because it was 5 cycles looped with no reset
    between halves - that is now an option, not the forced default.
 4. RESET is now COERCIVE-AWARE. Your P-E loop gives coercive ~ +24.5 V and
    -11.4 V, so a -3 V reset did nothing. Default reset is now -15 V.
 5. READ VOLTAGE default raised to 3 V. At 0.5-1.5 V your current sits in the
    noise floor; 3 V is the lowest read that clears it for this thick film.
 6. WRITE/SET default raised to +22 V (above the +24.5 V-ish coercive region
    but inside the compliance-safe window you found in Sheet3 of p1).
    DEPRESS default -14 V (above the -11.4 V negative coercive).

 SAFETY / WINDOW NOTES (from your own data)
 ------------------------------------------
 * Safe sweep/pulse window found experimentally: about -15 V to +25 V at
   100 uA compliance (your "Sheet3"). Going to +-35 V hit compliance and at
   10 mA the device degraded. DO NOT sweep to +-35 V on the 2602.
 * Full polarization saturation needs ~ +-37 V -> do that ONLY on the Polyk,
   never on the 2602.
 * Confirm the 2602 can source your chosen write V and keep compliance set.
   If current pins at the compliance value during a sweep, LOWER the voltage,
   do not raise compliance into the mA range.

 CONVENTION: +V on smua HI = +bias on Pt top electrode; FTO grounded.
===============================================================================


===============================================================================
0. RESET HELPER  (load this FIRST, once per session)
===============================================================================
-- Coercive-aware reset: poles the device past its negative coercive voltage
-- to a known low-conductance baseline, settles, then logs baseline G.
-- Defaults are sized to YOUR device (coercive ~ +24.5 / -11.4 V).

function reset_device(resetV, resetWidth, nReset, settleTime, readV)
    resetV     = resetV     or -15     -- reset amplitude (V): MUST exceed -|Vc-|
    resetWidth = resetWidth or 0.1     -- reset pulse width (s)
    nReset     = nReset     or 5       -- number of reset pulses
    settleTime = settleTime or 5       -- relaxation wait after reset (s)
    readV      = readV      or 3       -- read voltage to log baseline (V)

    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
    smua.source.limiti = 1e-3

    print("# RESET: V=" .. resetV .. "V  width=" .. resetWidth .. "s  n=" .. nReset
          .. "  settle=" .. settleTime .. "s  readV=" .. readV .. "V")

    for i = 1, nReset do
        smua.source.levelv = resetV
        delay(resetWidth)
        smua.source.levelv = 0
        delay(resetWidth)
    end

    smua.source.levelv = 0
    delay(settleTime)

    smua.source.levelv = readV
    delay(0.05)
    local i0 = smua.measure.i()
    smua.source.levelv = 0
    print(string.format("# RESET done. Baseline: I=%g A  G=%g uS", i0, (i0/readV)*1e6))
    smua.source.output = smua.OUTPUT_OFF
end

-- standalone:  reset_device()
===============================================================================


===============================================================================
1. BIPOLAR I-V SWEEP  (RUN THIS FIRST - reference + operating window)
===============================================================================
-- Multiple loops. Use to (a) confirm wake-up settled (loop-to-loop change in
-- current at +vTop < ~5%) and (b) read off the voltage where current clears
-- the noise floor, which sets your read/write voltages below.
-- KEEP vTop within your safe window (<= ~25 V at 100 uA compliance).

function run_IV(nCycles, vTop, vStep, settle, iLimit)
    nCycles = nCycles or 5
    vTop    = vTop    or 25      -- safe top (your Sheet3 window). NOT 35.
    vStep   = vStep   or 0.5
    settle  = settle  or 0.01
    iLimit  = iLimit  or 100e-6  -- 100 uA. Do NOT raise into mA range.

    smua.reset()
    smua.measure.nplc = 1
    smua.measure.filter.count = 5
    smua.measure.filter.enable = smua.FILTER_ON
    smua.measure.filter.type = smua.FILTER_REPEAT_AVG
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.limiti = iLimit
    smua.source.rangev = 40           -- allow high source range; keep iLimit low
    smua.nvbuffer1.clear()
    smua.nvbuffer1.appendmode = 1
    smua.source.output = smua.OUTPUT_ON

    print("# TEST: Bipolar I-V")
    print(string.format("# PARAMS: nCycles=%d  vTop=%g V  vStep=%g V  settle=%g s  iLimit=%g A",
          nCycles, vTop, vStep, settle, iLimit))
    print("Cycle", "Voltage(V)", "Current(A)")

    for cycle = 1, nCycles do
        for v = 0, vTop, vStep do
            smua.source.levelv = v; delay(settle)
            print(string.format("%d\t%g\t%g", cycle, v, smua.measure.i(smua.nvbuffer1)))
        end
        for v = vTop, -vTop, -vStep do
            smua.source.levelv = v; delay(settle)
            print(string.format("%d\t%g\t%g", cycle, v, smua.measure.i(smua.nvbuffer1)))
        end
        for v = -vTop, 0, vStep do
            smua.source.levelv = v; delay(settle)
            print(string.format("%d\t%g\t%g", cycle, v, smua.measure.i(smua.nvbuffer1)))
        end
    end

    smua.source.levelv = 0
    smua.source.output = smua.OUTPUT_OFF
    print("# Sweep complete.")
end

-- EXECUTE: 5 loops, +/-25 V, 0.5 V step, 100 uA compliance
run_IV(5, 25, 0.5, 0.01, 100e-6)
===============================================================================


===============================================================================
2. EPSC (Excitatory Post-Synaptic Current)
===============================================================================
-- Single pulse -> watch decay. writeV must exceed coercive to switch.
-- readV must clear the noise floor (3 V for this device).

function run_EPSC(amp, readV, pulseWidth, decayPoints, decayInterval)
    reset_device()

    amp           = amp           or 22
    readV         = readV         or 3
    pulseWidth    = pulseWidth    or 0.1
    decayPoints   = decayPoints   or 200
    decayInterval = decayInterval or 0.1

    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
    smua.source.limiti = 1e-3

    smua.nvbuffer1.clear()
    smua.nvbuffer1.appendmode = 1
    smua.nvbuffer1.collecttimestamps = 1

    print("# TEST: EPSC")
    print(string.format("# PARAMS: writeV=%g V  readV=%g V  pulseWidth=%g s  decayPoints=%d  decayInterval=%g s",
          amp, readV, pulseWidth, decayPoints, decayInterval))

    print("Status: Measuring Baseline...")
    smua.source.levelv = readV
    for i = 1, 20 do smua.measure.i(smua.nvbuffer1); delay(0.1) end

    smua.source.levelv = amp
    delay(pulseWidth)
    smua.measure.i(smua.nvbuffer1)

    print("Status: Measuring Decay...")
    smua.source.levelv = readV
    for i = 1, decayPoints do smua.measure.i(smua.nvbuffer1); delay(decayInterval) end

    smua.source.output = smua.OUTPUT_OFF

    print("Time(s)", "Current(A)", "Conductance(uS)")
    t_start = smua.nvbuffer1.timestamps[1]
    for i = 1, smua.nvbuffer1.n do
        t_rel = smua.nvbuffer1.timestamps[i] - t_start
        curr  = smua.nvbuffer1.readings[i]
        print(string.format("%g\t%g\t%g", t_rel, curr, (curr/readV)*1e6))
    end
end

-- EXECUTE: 22 V write, 3 V read
run_EPSC(22, 3, 0.1, 200, 0.1)
-- threshold scan (separate runs): vary amp to find synaptic threshold
-- run_EPSC(15, 3, 0.1, 200, 0.1)
-- run_EPSC(25, 3, 0.1, 200, 0.1)
===============================================================================


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
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
    smua.source.limiti = 1e-3

    smua.nvbuffer1.clear()
    smua.nvbuffer1.appendmode = 1
    smua.nvbuffer1.collecttimestamps = 1

    print("# TEST: PPF")
    print(string.format("# PARAMS: writeV=%g V  readV=%g V  pulseWidth=%g s  deltaT=%g s  decayTime=%g s",
          amp, readV, pulseWidth, deltaT, decayTime))

    smua.source.levelv = readV
    for i = 1, 40 do smua.measure.i(smua.nvbuffer1); delay(0.05) end

    smua.source.levelv = amp
    delay(pulseWidth)
    local A1 = smua.measure.i(smua.nvbuffer1)

    smua.source.levelv = readV
    delay(deltaT)

    smua.source.levelv = amp
    delay(pulseWidth)
    local A2 = smua.measure.i(smua.nvbuffer1)

    smua.source.levelv = readV
    local decayPoints = decayTime / 0.1
    for i = 1, decayPoints do smua.measure.i(smua.nvbuffer1); delay(0.1) end

    smua.source.output = smua.OUTPUT_OFF

    local ppf = 0
    if A1 ~= 0 then ppf = ((A2 - A1) / A1) * 100 end
    print(string.format("# RESULT: A1=%g A  A2=%g A  PPF_index=%g %%", A1, A2, ppf))

    print("Time(s)", "Current(A)", "Conductance(uS)")
    t_start = smua.nvbuffer1.timestamps[1]
    for i = 1, smua.nvbuffer1.n do
        t_now = smua.nvbuffer1.timestamps[i] - t_start
        curr  = smua.nvbuffer1.readings[i]
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
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
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
        train_currents[i] = smua.measure.i()
    end

    smua.source.output = smua.OUTPUT_OFF

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


===============================================================================
5. SDDP - Decay After Pulse
===============================================================================
-- Measures: 50 pulses of variable width, then watch decay
-- Plot: Time (x) vs Conductance (y)
-- Run separately with different pulseWidth

function run_SDDP_Decay(writeV, readV, pulseWidth, decayPoints, decayInterval)
    reset_device()                              -- your existing reset sweep

    writeV        = writeV        or 8
    readV         = readV         or 1.5
    pulseWidth    = pulseWidth    or 0.1
    decayPoints   = decayPoints   or 200
    decayInterval = decayInterval or 0.1

    local pulseCount = 50
    local pulseDelay = 0.05

    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
    smua.source.limiti = 1e-3

    smua.nvbuffer1.clear()
    smua.nvbuffer1.appendmode = 1
    smua.nvbuffer1.collecttimestamps = 1

    print("# TEST: SDDP-Decay")
    print(string.format("# PARAMS: writeV=%g V  readV=%g V  pulseWidth=%g s  pulseCount=%d  pulseDelay=%g s  decayPoints=%d  decayInterval=%g s",
          writeV, readV, pulseWidth, pulseCount, pulseDelay, decayPoints, decayInterval))

    -- BASELINE
    smua.source.levelv = readV
    for i = 1, 20 do
        smua.measure.i(smua.nvbuffer1)
        delay(0.1)
    end

    -- 50 WRITE PULSES
    for p = 1, pulseCount do
        smua.source.levelv = writeV
        delay(pulseWidth)

        smua.source.levelv = 0
        delay(pulseDelay)
    end

    -- DECAY
    smua.source.levelv = readV
    for i = 1, decayPoints do
        smua.measure.i(smua.nvbuffer1)
        delay(decayInterval)
    end

    smua.source.output = smua.OUTPUT_OFF

    print("Time(s)", "Current(A)", "Conductance(uS)")
    t_start = smua.nvbuffer1.timestamps[1]
    for i = 1, smua.nvbuffer1.n do
        t    = smua.nvbuffer1.timestamps[i] - t_start
        curr = smua.nvbuffer1.readings[i]
        print(string.format("%g\t%g\t%g", t, curr, (curr/readV)*1e6))
    end
end

-- EXECUTE: run each separately
run_SDDP_Decay(8, 1.5, 0.1, 200, 0.1)
-- run_SDDP_Decay(8, 1.5, 0.2, 200, 0.1)
-- run_SDDP_Decay(8, 1.5, 0.3, 200, 0.1)
-- run_SDDP_Decay(8, 1.5, 0.4, 200, 0.1)
-- run_SDDP_Decay(8, 1.5, 0.5, 200, 0.1)
===============================================================================


===============================================================================
6. SRDP (Spike-Rate Dependent Plasticity)
===============================================================================
function avg_read_current(readV, n, delayTime)
    local sum = 0
    smua.source.levelv = readV
    delay(delayTime)

    for i = 1, n do
        sum = sum + smua.measure.i()
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
        print("# ERROR: pulseWidth is longer than or equal to period.")
        print(string.format("# frequency=%g Hz  period=%g s  pulseWidth=%g s",
              frequency, period, pulseWidth))
        return
    end

    if offGap < 0.02 then
        print("# ERROR: offGap is too short for reliable SRDP.")
        print(string.format("# frequency=%g Hz  period=%g s  pulseWidth=%g s  offGap=%g s",
              frequency, period, pulseWidth, offGap))
        print("# Reduce pulseWidth. Do not clamp the gap.")
        return
    end

    reset_device()

    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
    smua.source.limiti = 1e-3

    print("# TEST: SRDP clean")
    print(string.format("# PARAMS: writeV=%g V  readV=%g V  pulseWidth=%g s  pulseCount=%d  frequency=%g Hz  offGap=%g s",
          writeV, readV, pulseWidth, pulseCount, frequency, offGap))

    -- Initial non-disturbing read
    local I0 = avg_read_current(readV, 5, 0.05)
    local G0 = (I0 / readV) * 1e6

    -- Pulse train: write pulse then 0 V gap
    for i = 1, pulseCount do
        smua.source.levelv = writeV
        delay(pulseWidth)

        smua.source.levelv = 0
        delay(offGap)
    end

    -- Let transient settle
    smua.source.levelv = 0
    delay(postWait)

    -- Final read
    local I_after = avg_read_current(readV, 5, 0.05)
    local G_after = (I_after / readV) * 1e6

    local idx = 0
    if G0 ~= 0 then
        idx = ((G_after - G0) / G0) * 100
    end

    print("Frequency(Hz)\tG0(uS)\tG_after(uS)\tSRDP_index(%)")
    print(string.format("%g\t%g\t%g\t%g", frequency, G0, G_after, idx))

    smua.source.output = smua.OUTPUT_OFF
end


-- Recommended runs
run_SRDP(22, 1, 0.02, 50, 2.0, 0.5)
-- run_SRDP(22, 1, 0.02, 50, 4.0, 0.5)
-- run_SRDP(22, 1, 0.02, 50, 6.0, 0.5)
-- run_SRDP(22, 1, 0.02, 50, 8.0, 0.5)
-- run_SRDP(22, 1, 0.02, 50, 10.0, 0.5)
================================================================
================================================================
function avg_read_current(readV, n, delayTime)
    local sum = 0
    smua.source.levelv = readV
    delay(delayTime)

    for i = 1, n do
        sum = sum + smua.measure.i()
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
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
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

        local curr = smua.measure.i()
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
end


run_SRDP(22, 1, 0.02, 50, 2.0, 0.5)
-- run_SRDP(22, 1, 0.02, 50, 4.0, 0.5)
-- run_SRDP(22, 1, 0.02, 50, 6.0, 0.5)
-- run_SRDP(22, 1, 0.02, 50, 8.0, 0.5)
-- run_SRDP(22, 1, 0.02, 50, 10.0, 0.5)
===============================================================================


===============================================================================
7. STDP (Spike-Timing Dependent Plasticity)   *** SIGN BUG FIXED ***
===============================================================================
-- ============================================================
-- FINAL TUNED STDP-LIKE TEST
--
-- Main changes compared with previous code:
-- 1) Lower start target current from 6e-7 A to 4e-7 A
--    so the device has room for potentiation.
-- 2) STDP pair changed to:
--       Vpos = +30 V
--       Vneg = -7 V
--       pulseWidth = 0.1 s
-- 3) Conditioning remains controlled and stops safely.
--
-- Plot:
--   signed_gap_s versus DeltaG_percent
-- ============================================================


function setup_SMU_STDP_FINAL()
    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON

    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-5

    smua.source.limiti = 1e-3
    smua.source.levelv = 0
    delay(0.5)
end


function read_current_avg_FINAL(readV, nread)
    readV = readV or 3.5
    nread = nread or 10

    smua.source.levelv = readV
    delay(0.7)

    local isum = 0
    for i = 1, nread do
        isum = isum + smua.measure.i()
        delay(0.05)
    end

    local iavg = isum / nread

    smua.source.levelv = 0
    delay(0.5)

    return iavg
end


function reset_STDP_FINAL(resetV, resetWidth, resetCount, settleTime, readV)
    resetV = resetV or -8
    resetWidth = resetWidth or 0.1
    resetCount = resetCount or 1
    settleTime = settleTime or 20
    readV = readV or 3.5

    setup_SMU_STDP_FINAL()

    print(string.format("RESET FINAL: V=%g V  width=%g s  n=%d  settle=%g s",
        resetV, resetWidth, resetCount, settleTime))

    for i = 1, resetCount do
        smua.source.levelv = resetV
        delay(resetWidth)

        smua.source.levelv = 0
        delay(0.5)
    end

    delay(settleTime)

    local I_after_reset = read_current_avg_FINAL(readV, 10)
    local G_after_reset = math.abs(I_after_reset / readV) * 1e6

    print(string.format("AFTER RESET: I=%g A  G=%g uS",
        I_after_reset, G_after_reset))

    smua.source.levelv = 0
    smua.source.output = smua.OUTPUT_OFF
end


function condition_to_target_current_FINAL(targetI, maxI, setV, setWidth, maxPulses, readV)
    targetI = targetI or 4e-7
    maxI = maxI or 8e-7
    setV = setV or 25
    setWidth = setWidth or 0.1
    maxPulses = maxPulses or 20
    readV = readV or 3.5

    setup_SMU_STDP_FINAL()

    print(string.format("FINAL CONDITIONING: targetI=%g A  maxI=%g A  setV=%g V  width=%g s  maxPulses=%d",
        targetI, maxI, setV, setWidth, maxPulses))

    local I_now = read_current_avg_FINAL(readV, 10)
    local G_now = math.abs(I_now / readV) * 1e6

    print(string.format("BEFORE CONDITIONING: I=%g A  G=%g uS",
        I_now, G_now))

    local p = 0

    while math.abs(I_now) < targetI and p < maxPulses do
        p = p + 1

        smua.source.levelv = setV
        delay(setWidth)

        smua.source.levelv = 0
        delay(0.7)

        I_now = read_current_avg_FINAL(readV, 10)
        G_now = math.abs(I_now / readV) * 1e6

        print(string.format("CONDITION pulse %d: I=%g A  G=%g uS",
            p, I_now, G_now))

        if math.abs(I_now) >= maxI then
            print("CONDITIONING stopped because current crossed maxI")
            break
        end
    end

    if math.abs(I_now) < targetI then
        print("WARNING: target current was not reached")
    end

    smua.source.levelv = 0
    smua.source.output = smua.OUTPUT_OFF

    print(string.format("CONDITIONING DONE: pulses=%d  I=%g A  G=%g uS",
        p, I_now, G_now))
end


function prepare_STDP_start_state_FINAL()
    reset_STDP_FINAL(-8, 0.1, 1, 20, 3.5)

    condition_to_target_current_FINAL(
        4e-7,
        8e-7,
        25,
        0.1,
        20,
        3.5
    )

    delay(1)
end


function run_STDP_Point_FINAL(dt_gap, order_mode, Vpos, Vneg_abs, readV, pulseWidth)
    dt_gap = math.abs(dt_gap or 0.1)

    Vpos = math.abs(Vpos or 30)
    Vneg_abs = math.abs(Vneg_abs or 7)

    readV = readV or 3.5
    pulseWidth = pulseWidth or 0.1

    if order_mode ~= 1 and order_mode ~= 2 then
        print("ERROR: order_mode must be 1 or 2")
        return
    end

    local Vneg = -Vneg_abs

    local signed_gap = dt_gap
    if order_mode == 2 then
        signed_gap = -dt_gap
    end

    local actual_start_dt = pulseWidth + dt_gap
    if order_mode == 2 then
        actual_start_dt = -actual_start_dt
    end

    prepare_STDP_start_state_FINAL()

    setup_SMU_STDP_FINAL()

    print("TEST FINAL STDP point")
    print(string.format("PARAMS: signed_gap=%g s  actual_start_dt=%g s  mode=%d  Vpos=%g V  Vneg=%g V  readV=%g V  pulseWidth=%g s",
        signed_gap, actual_start_dt, order_mode, Vpos, Vneg, readV, pulseWidth))

    local I_initial = read_current_avg_FINAL(readV, 10)
    local G_initial = math.abs(I_initial / readV) * 1e6

    print(string.format("START STATE BEFORE PAIR: I_init=%g A  G_init=%g uS",
        I_initial, G_initial))

    smua.source.levelv = 0
    delay(0.5)

    if order_mode == 1 then
        smua.source.levelv = Vpos
        delay(pulseWidth)

        smua.source.levelv = 0
        delay(dt_gap)

        smua.source.levelv = Vneg
        delay(pulseWidth)
    else
        smua.source.levelv = Vneg
        delay(pulseWidth)

        smua.source.levelv = 0
        delay(dt_gap)

        smua.source.levelv = Vpos
        delay(pulseWidth)
    end

    smua.source.levelv = 0
    delay(1.0)

    local I_final = read_current_avg_FINAL(readV, 10)
    local G_final = math.abs(I_final / readV) * 1e6

    smua.source.levelv = 0
    smua.source.output = smua.OUTPUT_OFF

    local DeltaI = 0
    local DeltaG = 0

    if math.abs(I_initial) > 1e-12 then
        DeltaI = ((I_final - I_initial) / math.abs(I_initial)) * 100
    end

    if math.abs(G_initial) > 1e-12 then
        DeltaG = ((G_final - G_initial) / math.abs(G_initial)) * 100
    end

    print("signed_gap_s actual_start_dt_s Order I_init_A I_final_A G_init_uS G_final_uS DeltaI_percent DeltaG_percent")
    print(string.format("%g\t%g\t%d\t%g\t%g\t%g\t%g\t%g\t%g",
        signed_gap, actual_start_dt, order_mode,
        I_initial, I_final,
        G_initial, G_final,
        DeltaI, DeltaG))
end


function run_STDP_Sweep_FINAL()
    print("FINAL STDP sweep started")
    print("Goal: start every point near I_init = 4e-7 A if device allows")
    print("Conditioning: +25 V, 0.1 s, max 20 pulses")
    print("STDP pair: Vpos=30 V, Vneg=-7 V, readV=3.5 V, pulseWidth=0.1 s")
    print("Reset: -8 V, 0.1 s, 1 pulse, 20 s settle")
    print("Plot signed_gap_s versus DeltaG_percent")
    print("Interleaved order: +gap then -gap")

    run_STDP_Point_FINAL(0.05, 1, 30, 7, 3.5, 0.1)
    run_STDP_Point_FINAL(0.05, 2, 30, 7, 3.5, 0.1)

    run_STDP_Point_FINAL(0.1, 1, 30, 7, 3.5, 0.1)
    run_STDP_Point_FINAL(0.1, 2, 30, 7, 3.5, 0.1)

    run_STDP_Point_FINAL(0.2, 1, 30, 7, 3.5, 0.1)
    run_STDP_Point_FINAL(0.2, 2, 30, 7, 3.5, 0.1)

    run_STDP_Point_FINAL(0.5, 1, 30, 7, 3.5, 0.1)
    run_STDP_Point_FINAL(0.5, 2, 30, 7, 3.5, 0.1)

    run_STDP_Point_FINAL(1.0, 1, 30, 7, 3.5, 0.1)
    run_STDP_Point_FINAL(1.0, 2, 30, 7, 3.5, 0.1)

    run_STDP_Point_FINAL(2.0, 1, 30, 7, 3.5, 0.1)
    run_STDP_Point_FINAL(2.0, 2, 30, 7, 3.5, 0.1)

    run_STDP_Point_FINAL(5.0, 1, 30, 7, 3.5, 0.1)
    run_STDP_Point_FINAL(5.0, 2, 30, 7, 3.5, 0.1)

    print("FINAL STDP sweep finished")
end


function run_ONE_TEST_FINAL()
    print("Running one test point only")
    print("STDP pair: Vpos=30 V, Vneg=-7 V, readV=3.5 V, pulseWidth=0.1 s")
    run_STDP_Point_FINAL(0.05, 1, 30, 7, 3.5, 0.1)
end


run_STDP_Sweep_FINAL()

-- For only one test point, comment the above line and uncomment this:
-- run_ONE_TEST_FINAL()
===============================================================================


===============================================================================
8. SNDP (Spike-Number Dependent Plasticity)
===============================================================================
-- SNDP: Spike-Number-Dependent Plasticity
-- Corrected sequence:
--   reset_device()
--   baseline read
--   for each pulse:
--       write pulse -> 0 V gap -> short read -> 0 V gap
--   decay:
--       0 V wait -> short read -> 0 V
--
-- Plot:
--   TRAIN: Pulse# vs Conductance
--   DECAY: Time vs Conductance
-- ============================================================


-- =======================
-- EDIT ONLY THIS BLOCK
-- =======================
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
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON

    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = SNDP_CFG.measureRange

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
        isum = isum + smua.measure.i()
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

    print("# SNDP corrected test finished")
end


-- =======================
-- EXECUTE
-- =======================
run_SNDP()
===============================================================================


===============================================================================
9. MULTI-LEVEL CONDUCTANCE STATES
===============================================================================
function run_MultiLevel_FIXED(writeV, readV, pulseWidth, pulsesPerLevel, nLevels)
    writeV         = writeV         or 25
    readV          = readV          or 3.5
    pulseWidth     = pulseWidth     or 0.1
    pulsesPerLevel = pulsesPerLevel or 20
    nLevels        = nLevels        or 10

    reset_device()

    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
    smua.source.limiti = 1e-3
    smua.source.levelv = 0
    delay(1)

    print("TEST: Multi-Level Conductance States FIXED")
    print(string.format("PARAMS: writeV=%g V  readV=%g V  pulseWidth=%g s  pulsesPerLevel=%d  nLevels=%d  totalPulses=%d",
          writeV, readV, pulseWidth, pulsesPerLevel, nLevels, pulsesPerLevel * nLevels))

    print("Pulse\tLevel\tCurrent_A\tConductance_uS")

    local cum = 0

    for L = 1, nLevels do
        for p = 1, pulsesPerLevel do
            cum = cum + 1

            -- Write pulse
            smua.source.levelv = writeV
            delay(pulseWidth)

            -- Return to zero before read
            smua.source.levelv = 0
            delay(0.2)

            -- Read and average current
            smua.source.levelv = readV
            delay(0.1)

            local isum = 0
            local nread = 5

            for r = 1, nread do
                isum = isum + smua.measure.i()
                delay(0.02)
            end

            local curr = isum / nread
            local conductance = math.abs(curr / readV) * 1e6

            print(string.format("%d\t%d\t%g\t%g", cum, L, curr, conductance))

            -- Return to zero after read
            smua.source.levelv = 0
            delay(0.2)
        end
    end

    smua.source.levelv = 0
    smua.source.output = smua.OUTPUT_OFF
end


run_MultiLevel_FIXED(25, 3.5, 0.1, 20, 10)
===============================================================================


===============================================================================
10. POTENTIATION / DEPRESSION (LTP/LTD)   *** FIXED ***
===============================================================================
-- Clean version: ONE potentiation block (positive pulses, G should rise)
-- then a RESET + relaxation, then ONE depression block (negative pulses,
-- G should fall). This is the proper P&D shape.
--
-- WHY YOUR OLD DATA OSCILLATED: it ran cycles=5 of (50 pos + 50 neg) with NO
-- reset between halves, so each block inherited the previous block's state
-- and you got jump-then-decay every 50 pulses instead of a clean rise/fall.
--
-- midReset = true  -> reset + wait between potentiation and depression (clean)
-- cycles   = how many pot/dep cycles to record (use 1 for the clean figure;
--            use >1 only if you specifically want a cyclic-endurance P&D plot)

function run_LTP_LTD(cycles, posV, negV, readV, pulseWidth, readGap, midReset, midWait)
    reset_device()

    cycles     = cycles     or 1            -- DEFAULT 1 clean cycle now
    posV       = posV       or 22           -- potentiation amplitude (V)
    negV       = negV       or -14          -- depression amplitude (V)
    readV      = readV      or 3
    pulseWidth = pulseWidth or 0.1
    readGap    = readGap    or 0.05
    if midReset == nil then midReset = true end
    midWait    = midWait    or 3            -- relaxation wait after mid reset (s)

    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
    smua.source.limiti = 1e-3

    smua.nvbuffer1.clear()
    smua.nvbuffer1.appendmode = 1
    smua.nvbuffer1.collecttimestamps = 1

    print("# TEST: LTP/LTD (Potentiation/Depression)")
    print(string.format("# PARAMS: cycles=%d  posV=%g V  negV=%g V  readV=%g V  pulseWidth=%g s  readGap=%g s  midReset=%s  midWait=%g s",
          cycles, posV, negV, readV, pulseWidth, readGap, tostring(midReset), midWait))

    smua.source.levelv = readV
    delay(1)

    for k = 1, cycles do
        -- POTENTIATION block
        for i = 1, 50 do
            smua.source.levelv = posV; delay(pulseWidth)
            smua.source.levelv = readV; delay(readGap)
            smua.measure.i(smua.nvbuffer1)
        end

        -- MID RESET between halves (the fix). Resets state + lets it relax,
        -- so depression starts from a defined point, not the potentiated tail.
        if midReset then
            smua.source.output = smua.OUTPUT_OFF
            reset_device()                 -- coercive-aware reset
            smua.reset()
            smua.source.func = smua.OUTPUT_DCVOLTS
            smua.source.output = smua.OUTPUT_ON
            smua.measure.autorangei = smua.AUTORANGE_OFF
            smua.measure.rangei = 1e-4
            smua.source.limiti = 1e-3
            smua.source.levelv = readV
            delay(midWait)
        end

        -- DEPRESSION block
        for i = 1, 50 do
            smua.source.levelv = negV; delay(pulseWidth)
            smua.source.levelv = readV; delay(readGap)
            smua.measure.i(smua.nvbuffer1)
        end
    end

    smua.source.output = smua.OUTPUT_OFF

    print("Pulse#", "Current(A)", "Conductance(uS)")
    for i = 1, smua.nvbuffer1.n do
        curr = smua.nvbuffer1.readings[i]
        print(string.format("%d\t%g\t%g", i, curr, (curr/readV)*1e6))
    end
end

-- EXECUTE: clean single cycle (50 pot + reset + 50 dep)
run_LTP_LTD(1, 22, -14, 3, 0.1, 0.05, true, 3)
-- cyclic version WITHOUT mid-reset (only if you want the repeatability plot):
-- run_LTP_LTD(5, 22, -14, 3, 0.1, 0.05, false, 3)
===============================================================================


===============================================================================
11. RETENTION - SINGLE STATE  (LTM proof, >=1000 s)
===============================================================================
function run_Retention_Single(statePulses, writeV, readV, pulseWidth, t_total, t_step)
    reset_device()

    statePulses = statePulses or 30
    writeV      = writeV      or 22
    readV       = readV       or 3
    pulseWidth  = pulseWidth  or 0.1
    t_total     = t_total     or 1000
    t_step      = t_step      or 10

    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
    smua.source.limiti = 1e-3

    print("# TEST: Retention (single state)")
    print(string.format("# PARAMS: statePulses=%d  writeV=%g V  readV=%g V  pulseWidth=%g s  t_total=%g s  t_step=%g s",
          statePulses, writeV, readV, pulseWidth, t_total, t_step))

    for p = 1, statePulses do
        smua.source.levelv = writeV; delay(pulseWidth)
        smua.source.levelv = 0;      delay(pulseWidth)
    end

    print("Time(s)", "Current(A)", "Conductance(uS)")
    local t0 = os.time()
    local el = 0
    while el <= t_total do
        smua.source.levelv = readV; delay(0.05)
        local curr = smua.measure.i()
        print(string.format("%d\t%g\t%g", el, curr, (curr/readV)*1e6))
        smua.source.levelv = 0
        delay(t_step)
        el = os.time() - t0
    end

    smua.source.output = smua.OUTPUT_OFF
end

-- EXECUTE
run_Retention_Single(30, 22, 3, 0.1, 1000, 10)
===============================================================================


===============================================================================
12. RETENTION - MULTI-STATE
===============================================================================
function run_Retention_Multi(writeV, readV, pulseWidth, t_total, t_step, levelsTable)
    writeV     = writeV     or 22
    readV      = readV      or 3
    pulseWidth = pulseWidth or 0.1
    t_total    = t_total    or 1000
    t_step     = t_step     or 10
    levelsTable = levelsTable or {10, 30, 60}

    print("# TEST: Retention (multi-state)")
    print(string.format("# PARAMS: writeV=%g V  readV=%g V  pulseWidth=%g s  t_total=%g s  t_step=%g s  nLevels=%d",
          writeV, readV, pulseWidth, t_total, t_step, #levelsTable))
    print("State", "Time(s)", "Current(A)", "Conductance(uS)")

    for s = 1, #levelsTable do
        reset_device()
        smua.reset()
        smua.source.func = smua.OUTPUT_DCVOLTS
        smua.source.output = smua.OUTPUT_ON
        smua.measure.autorangei = smua.AUTORANGE_OFF
        smua.measure.rangei = 1e-4
        smua.source.limiti = 1e-3

        for p = 1, levelsTable[s] do
            smua.source.levelv = writeV; delay(pulseWidth)
            smua.source.levelv = 0;      delay(pulseWidth)
        end

        local t0 = os.time()
        local el = 0
        while el <= t_total do
            smua.source.levelv = readV; delay(0.05)
            local curr = smua.measure.i()
            print(string.format("%d\t%d\t%g\t%g", s, el, curr, (curr/readV)*1e6))
            smua.source.levelv = 0
            delay(t_step)
            el = os.time() - t0
        end
        smua.source.output = smua.OUTPUT_OFF
    end
end

-- EXECUTE: 3 states (10, 30, 60 pulses), 1000 s each
run_Retention_Multi(22, 3, 0.1, 1000, 10, {10, 30, 60})
===============================================================================


===============================================================================
13. ENDURANCE  (gentle, pre-conditioned; NOT a stress test)
===============================================================================
function run_Endurance(setV, resetV, srWidth, readV, nPrecond, nCycles)
    reset_device()

    setV     = setV     or 22       -- SET above +Vc (but within safe window)
    resetV   = resetV   or -14      -- RESET above -Vc
    srWidth  = srWidth  or 0.05
    readV    = readV    or 3
    nPrecond = nPrecond or 20
    nCycles  = nCycles  or 100       -- keep modest; device degrades past ~5000

    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
    smua.source.limiti = 1e-3

    print("# TEST: Endurance (gentle, pre-conditioned)")
    print(string.format("# PARAMS: setV=%g V  resetV=%g V  srWidth=%g s  readV=%g V  nPrecond=%d  nCycles=%d",
          setV, resetV, srWidth, readV, nPrecond, nCycles))

    for c = 1, nPrecond do
        smua.source.levelv = setV;   delay(srWidth)
        smua.source.levelv = resetV; delay(srWidth)
    end
    smua.source.levelv = 0; delay(1)

    print("Cycle", "HRS_Current(A)", "LRS_Current(A)", "On_Off_Ratio")
    for c = 1, nCycles do
        smua.source.levelv = setV; delay(srWidth)
        smua.source.levelv = readV; delay(0.02)
        local lrs = smua.measure.i()
        smua.source.levelv = resetV; delay(srWidth)
        smua.source.levelv = readV;  delay(0.02)
        local hrs = smua.measure.i()
        local ratio = 0
        if hrs ~= 0 then ratio = math.abs(lrs / hrs) end
        print(string.format("%d\t%g\t%g\t%g", c, hrs, lrs, ratio))
    end

    smua.source.output = smua.OUTPUT_OFF
end

-- EXECUTE: 20 pre-condition + 100 logged cycles
run_Endurance(22, -14, 0.05, 3, 20, 100)
===============================================================================


===============================================================================
 RECOMMENDED ORDER (per fresh good electrode)
 -----------------------------------------------------------------------------
   0) load reset_device() once
   1) run_IV(5,25,0.5,...)        -> sweep FIRST; find window, confirm wake-up
   2) run_EPSC(...)               -> threshold + EPSC
   3) run_PPF(...)                -> all deltaT
   4) run_SDDP / run_SDDP_Decay   -> all widths
   5) run_SRDP(...)               -> all frequencies (reset each call)
   6) run_STDP_Point(...)         -> all dt, both modes (signed dt now)
   7) run_SNDP(...)               -> all N
   8) run_MultiLevel(...)         -> 10-state staircase
   9) run_LTP_LTD(1,...)          -> clean single-cycle P&D (mid-reset on)
  10) run_Retention_Single/Multi  -> retention >=1e3 s
  11) run_Endurance(...)          -> gentle endurance

 KEY REMINDERS
=============================================================================
FREQUENCY 
=============================================
-- ============================================================
-- FREQUENCY RESPONSE / RATE-DEPENDENT PLASTICITY TEST
--
-- Purpose:
--   Show pulse-rate-dependent conductance/current change.
--
-- Plot:
--   Pulse number vs Current
--   Pulse number vs Conductance
--
-- Important:
--   With pulseWidth = 0.1 s, do NOT test 100 Hz.
--   Practical frequencies: 0.5, 1, 2, 5 Hz.
-- ============================================================


function setup_SMU_FREQ()
    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON

    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4

    smua.source.limiti = 1e-3
    smua.source.levelv = 0
    delay(0.5)
end


function read_current_avg_FREQ(readV, nread)
    readV = readV or 3.5
    nread = nread or 5

    smua.source.levelv = readV
    delay(0.1)

    local isum = 0
    for r = 1, nread do
        isum = isum + smua.measure.i()
        delay(0.02)
    end

    local iavg = isum / nread

    smua.source.levelv = 0
    delay(0.1)

    return iavg
end


function run_FrequencyResponse_FIXED(frequency, numPulses, writeV, readV, pulseWidth)
    frequency = frequency or 1
    numPulses = numPulses or 20
    writeV = writeV or 25
    readV = readV or 3.5
    pulseWidth = pulseWidth or 0.1

    local period = 1 / frequency
    local gap = period - pulseWidth

    if gap <= 0 then
        print("ERROR: frequency is too high for this pulseWidth")
        print(string.format("Requested frequency = %g Hz", frequency))
        print(string.format("Period = %g s", period))
        print(string.format("pulseWidth = %g s", pulseWidth))
        print("Use lower frequency or shorter pulseWidth")
        return
    end

    reset_device()
    setup_SMU_FREQ()

    local actualPeriod = pulseWidth + gap
    local actualFrequency = 1 / actualPeriod

    print("TEST: Frequency Response / Rate-Dependent Plasticity")
    print(string.format("PARAMS: requestedFreq=%g Hz  actualFreq=%g Hz  writeV=%g V  readV=%g V  pulseWidth=%g s  gap=%g s  numPulses=%d",
        frequency, actualFrequency, writeV, readV, pulseWidth, gap, numPulses))

    local I0 = read_current_avg_FREQ(readV, 5)
    local G0 = math.abs(I0 / readV) * 1e6

    print(string.format("START: I0=%g A  G0=%g uS", I0, G0))
    print("Pulse\tFrequency_Hz\tCurrent_A\tConductance_uS\tDeltaG_percent")

    for i = 1, numPulses do
        -- write pulse
        smua.source.levelv = writeV
        delay(pulseWidth)

        -- zero gap before read
        smua.source.levelv = 0
        delay(gap)

        -- read state
        local curr = read_current_avg_FREQ(readV, 5)
        local cond = math.abs(curr / readV) * 1e6

        local deltaG = 0
        if math.abs(G0) > 1e-12 then
            deltaG = ((cond - G0) / math.abs(G0)) * 100
        end

        print(string.format("%d\t%g\t%g\t%g\t%g",
            i, actualFrequency, curr, cond, deltaG))
    end

    smua.source.levelv = 0
    smua.source.output = smua.OUTPUT_OFF
end


function run_FrequencyResponse_Sweep_FIXED()
    print("FREQUENCY RESPONSE SWEEP STARTED")
    print("Each frequency starts after reset_device()")

    run_FrequencyResponse_FIXED(0.5, 20, 25, 3.5, 0.1)
    run_FrequencyResponse_FIXED(1.0, 20, 25, 3.5, 0.1)
    run_FrequencyResponse_FIXED(2.0, 20, 25, 3.5, 0.1)
    run_FrequencyResponse_FIXED(5.0, 20, 25, 3.5, 0.1)

    print("FREQUENCY RESPONSE SWEEP FINISHED")
end


run_FrequencyResponse_Sweep_FIXED()
 -----------------------------------------------------------------------------
 * Adjust writeV/negV/readV to YOUR final measured coercive values. Defaults
   here (write +22, dep -14, read 3) come from your P-E loop + safe window.
 * If a sweep pins at compliance, LOWER vTop. Do NOT raise compliance to mA.
 * Full +-37 V polarization saturation belongs on the Polyk, not the 2602.
 * reset_device() default is now -15 V (coercive-aware). Pass your own value
   if your measured negative coercive differs, e.g. reset_device(-18).
===============================================================================
