

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
1. BIPOLAR I-V SWEEP 
===============================================================================
-- Use this for basic characterization before running synaptic tests
-- Reduced range, tighter compliance

smua.reset()
smu = smua
smu.measure.nplc = 1
smu.measure.filter.count = 5
smu.measure.filter.enable = smu.FILTER_ON
smu.measure.filter.type = smu.FILTER_REPEAT_AVG

smu.source.func = smu.OUTPUT_DCVOLTS
smu.source.limiti = 100e-6
smu.source.rangev = 10

smu.nvbuffer1.clear()
smu.nvbuffer1.appendmode = 1
smu.source.output = smu.OUTPUT_ON

for cycle = 1, 5 do
    for v = 0, 20, 0.5 do
        smu.source.levelv = v
        delay(0.01)
        print(cycle, v, smu.measure.i(smu.nvbuffer1))
    end
    for v = 20, -17, -0.5 do
        smu.source.levelv = v
        delay(0.01)
        print(cycle, v, smu.measure.i(smu.nvbuffer1))
    end
    for v = -17, 0, 0.5 do
        smu.source.levelv = v
        delay(0.01)
        print(cycle, v, smu.measure.i(smu.nvbuffer1))
    end
end

smu.source.output = smu.OUTPUT_OFF
print("Sweep Complete.")

===============================================================================
2. EPSC (Excitatory Post-Synaptic Current) 
===============================================================================
-- Measures: Baseline → Pulse → Current Decay
-- What to plot: Time (x) vs Current (y)
-- Expected: Sharp spike at pulse, then exponential decay to new baseline
reset_device()
function run_EPSC(amp, readV, pulseWidth, decayPoints, decayInterval)
    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON

    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
    smua.source.limiti = 1e-3  -- 1mA compliance

    smua.nvbuffer1.clear()
    smua.nvbuffer1.appendmode = 1
    smua.nvbuffer1.collecttimestamps = 1

    -- BASELINE (2 seconds)
    print("Status: Measuring Baseline...")
    smua.source.levelv = readV
    for i = 1, 20 do
        smua.measure.i(smua.nvbuffer1)
        delay(0.1)
    end

    -- STIMULUS PULSE
    smua.source.levelv = amp
    delay(pulseWidth)
    smua.measure.i(smua.nvbuffer1)  -- Capture peak

    -- POST-PULSE DECAY
    print("Status: Measuring Decay...")
    smua.source.levelv = readV
    for i = 1, decayPoints do
        smua.measure.i(smua.nvbuffer1)
        delay(decayInterval)
    end

    smua.source.output = smua.OUTPUT_OFF

    -- EXPORT
    print("Time(s)", "Current(A)")
    t_start = smua.nvbuffer1.timestamps[1]
    for i = 1, smua.nvbuffer1.n do
        t_rel = smua.nvbuffer1.timestamps[i] - t_start
        print(string.format("%g\t%g", t_rel, smua.nvbuffer1.readings[i]))
    end
end

-- EXECUTE: 8V write, 1.5V read, 100ms pulse, 200 decay points, 100ms interval
run_EPSC(8, 1.5, 0.1, 200, 0.1)


===============================================================================
3. PPF (Paired-Pulse Facilitation) 
===============================================================================
-- Measures: Two pulses separated by deltaT, compare A2/A1
-- What to plot: deltaT (x) vs PPF Index (A2/A1 * 100) (y)
-- Expected: PPF index decreases as deltaT increases
-- Run multiple times with different deltaT values
   reset_device()
function run_PPF(amp, readV, pulseWidth, deltaT, decayTime)
    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON

    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
    smua.source.limiti = 1e-3

    smua.nvbuffer1.clear()
    smua.nvbuffer1.appendmode = 1
    smua.nvbuffer1.collecttimestamps = 1

    -- BASELINE (2 seconds)
    print("Status: Measuring Baseline...")
    smua.source.levelv = readV
    for i = 1, 40 do
        smua.measure.i(smua.nvbuffer1)
        delay(0.05)
    end

    -- PULSE 1
    smua.source.levelv = amp
    delay(pulseWidth)
    smua.measure.i(smua.nvbuffer1)  -- Peak A1

    -- GAP — just wait, no measurement, so deltaT is accurate
    smua.source.levelv = readV
    delay(deltaT)

    -- PULSE 2
    smua.source.levelv = amp
    delay(pulseWidth)
    smua.measure.i(smua.nvbuffer1)  -- Peak A2

    -- DECAY
    print("Status: Measuring Decay...")
    smua.source.levelv = readV
    decayPoints = decayTime / 0.1
    for i = 1, decayPoints do
        smua.measure.i(smua.nvbuffer1)
        delay(0.1)
    end

    smua.source.output = smua.OUTPUT_OFF

    -- EXPORT
    print("Time(s)", "Current(A)")
    t_start = smua.nvbuffer1.timestamps[1]
    for i = 1, smua.nvbuffer1.n do
        t_now = smua.nvbuffer1.timestamps[i] - t_start
        print(string.format("%g\t%g", t_now, smua.nvbuffer1.readings[i]))
    end
end

-- EXECUTE: Run each line separately for different deltaT values
-- 8V write, 1.5V read, 100ms pulse, varying gap, 5s decay
run_PPF(8, 1.5, 0.1, 0.05, 5)
-- run_PPF(8, 1.5, 0.1, 0.1, 5)
-- run_PPF(8, 1.5, 0.1, 0.2, 5)
-- run_PPF(8, 1.5, 0.1, 0.3, 5)
-- run_PPF(8, 1.5, 0.1, 0.4, 5)
-- run_PPF(8, 1.5, 0.1, 0.5, 5)
-- run_PPF(8, 1.5, 0.1, 1.0, 5)


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
    decayPoints   = decayPoints   or 2000
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
run_SDDP_Decay(8, 1.5, 0.1, 2000, 0.1)
-- run_SDDP_Decay(8, 1.5, 0.2, 2000, 0.1)
-- run_SDDP_Decay(8, 1.5, 0.3, 2000, 0.1)
-- run_SDDP_Decay(8, 1.5, 0.4, 2000, 0.1)
-- run_SDDP_Decay(8, 1.5, 0.5, 2000, 0.1)
===============================================================================


===================================================
6. SRDP
===================================================
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
    pulseCount = pulseCount or 30
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
run_SRDP(22, 1, 0.02, 30, 2.0, 0.5)
-- run_SRDP(22, 1, 0.02, 30, 4.0, 0.5)
-- run_SRDP(22, 1, 0.02, 30, 6.0, 0.5)
-- run_SRDP(22, 1, 0.02, 30, 8.0, 0.5)

================================================================

7. Retention
================================================================
========================================================
-- Program a level with N pulses, then read at log-spaced times.
-- Plot: log10(Time) (x) vs Conductance (uS) (y)
-- Keithley 2602 Compatible

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
    c = smua.measure.i()
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
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
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

    print("Initial (post-reset) G = " ..
          string.format("%g", g0) .. " uS")

end

-------------------------------------------------
-- AUTOMATIC RETENTION SEQUENCE
-------------------------------------------------

run_Retention(100)
run_Retention(80)
run_Retention(60)
run_Retention(40)
run_Retention(20)

print("")
print("ALL RETENTION TESTS COMPLETED")
============================================================

8. Endurance
============================================================
function run_Endurance1500(numCycles)
    local posV = 18
    local negV = -14
    local readV = 1.5
    local pulseWidth = 0.1
    local gap = 0.05
    local pulses = 5
    local breakdownLimit = 50      -- uS; stop if Gplus exceeds this

    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.rangev = 20
    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-5
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
            isum = isum + smua.measure.i()
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
            isum = isum + smua.measure.i()
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
    print("Endurance test completed.")
end

run_Endurance1500(1500)


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
10. POTENTIATION / DEPRESSION TRAINING — Figure 3A
===============================================================================
-- Measures: 50 positive pulses (potentiation) then 50 negative (depression)
-- What to plot: Total pulse# (x) vs Conductance (y)
-- Expected: Conductance ramps up for 50 pulses, ramps down for 50

function run_LTP_LTD(cycles)
    posV = 8
    negV = -8
    readV = 1.5
    pulseWidth = 0.1
    readGap = 0.05

    smua.reset()
    smua.source.func = smua.OUTPUT_DCVOLTS
    smua.source.output = smua.OUTPUT_ON

    smua.measure.autorangei = smua.AUTORANGE_OFF
    smua.measure.rangei = 1e-4
    smua.source.limiti = 1e-3

    smua.nvbuffer1.clear()
    smua.nvbuffer1.appendmode = 1
    smua.nvbuffer1.collecttimestamps = 1

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
            smua.measure.i(smua.nvbuffer1)
        end

        -- DEPRESSION: 50 negative pulses
        for i = 1, 50 do
            smua.source.levelv = negV
            delay(pulseWidth)
            smua.source.levelv = readV
            delay(readGap)
            smua.measure.i(smua.nvbuffer1)
        end
    end

    smua.source.output = smua.OUTPUT_OFF

    -- EXPORT
    print("Pulse#", "Current(A)", "Conductance(uS)")
    for i = 1, smua.nvbuffer1.n do
        curr = smua.nvbuffer1.readings[i]
        cond = (curr / readV) * 1e6
        print(string.format("%d\t%g\t%g", i, curr, cond))
    end
end

-- EXECUTE: 1 cycles = 100 total pulses
run_LTP_LTD(1)


-- =============================================================================
11.  SNDP -- pulse WIDTH constant, pulse NUMBER varied.
-- =============================================================================
function run_SNDP_Decay(writeV, readV, pulseCount, decayPoints, decayInterval)
    reset_device()
    writeV        = writeV        or 8
    readV         = readV         or 1.5
    pulseCount    = pulseCount    or 50
    decayPoints   = decayPoints   or 1500
    decayInterval = decayInterval or 0.1
    local pulseWidth = 0.1
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
    print("# TEST: SNDP-Decay")
    print(string.format("# PARAMS: writeV=%g V  readV=%g V  pulseWidth=%g s  pulseCount=%d  pulseDelay=%g s  decayPoints=%d  decayInterval=%g s",
          writeV, readV, pulseWidth, pulseCount, pulseDelay, decayPoints, decayInterval))
    smua.source.levelv = readV
    for i = 1, 20 do
        smua.measure.i(smua.nvbuffer1)
        delay(0.1)
    end
    for p = 1, pulseCount do
        smua.source.levelv = writeV
        delay(pulseWidth)
        smua.source.levelv = 0
        delay(pulseDelay)
    end
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


-- =============================================================================
-- DRIVERS -- 300 s rest between runs
-- =============================================================================
function rest(chunks)
    local k
    for k = 1, chunks do
        delay(5)
    end
end

function run_SDDP_ALL(writeV, readV)
    writeV = writeV or 8
    readV  = readV  or 1.5
    local wlist = {0.1, 0.2, 0.3, 0.4, 0.5}
    local i
    print("# ===== SDDP SWEEP: pulse width varied, count fixed at 50 =====")
    for i = 1, table.getn(wlist) do
        print(string.format("# ---- run %d of %d : width %g s ----", i, table.getn(wlist), wlist[i]))
        run_SDDP_Decay(writeV, readV, wlist[i], 200, 0.1)
        if i < table.getn(wlist) then
            print("# resting 300 s")
            rest(60)
        end
    end
    print("# SDDP SWEEP complete")
end

function run_SNDP_ALL(writeV, readV)
    writeV = writeV or 8
    readV  = readV  or 1.5
    local nlist = {10, 20, 30, 40, 50}
    local i
    print("# ===== SNDP SWEEP: pulse count varied, width fixed at 0.1 s =====")
    for i = 1, table.getn(nlist) do
        print(string.format("# ---- run %d of %d : N = %d ----", i, table.getn(nlist), nlist[i]))
        run_SNDP_Decay(writeV, readV, nlist[i], 200, 0.1)
        if i < table.getn(nlist) then
            print("# resting 300 s")
            rest(60)
        end
    end
    print("# SNDP SWEEP complete")
end
====================================================
