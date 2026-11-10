========================================================
STDP
=========================================================
-- The two things that made STDP painful, fixed structurally: 
-- 1) baseline drift between points -> full reset before EVERY dt point, 
-- so each point starts from the same state. No closed loop needed. 
-- 2) one-point-per-run workflow -> this loops through all dt values in 
-- both orders automatically and prints one final table. 
-- dt floor is ~0.02s: below that, Lua overhead makes the real gap 
-- larger than requested. All dt values here are safely above it. 
-- What to plot: dt (x, negative for post-before-pre) vs DeltaW% (y). 

-- ⚡ RUNTIME FIX: Manual Absolute Value handler for pure Keithley Lua 5.0 compatibility
function absolute_value(val)
    if val < 0 then
        return -val
    else
        return val
    end
end

function run_STDP_Curve() 
    local writeV_Pos = 15 
    local writeV_Neg = -6 
    local readV = 1.0 
    local width = 0.1 
    
    local dt_list = {0.05, 0.1, 0.2, 0.3, 0.5, 1.0} 
    local total_dt = table.getn(dt_list) -- Legacy compliance fix
    
    smua.reset() 
    smua.source.func = smua.OUTPUT_DCVOLTS 
    smua.measure.autorangei = smua.AUTORANGE_OFF 
    
    -- High-resolution measurement range to track ~78 nA currents accurately
    smua.measure.rangei = 1e-6 
    smua.source.limiti = 1e-3 
    smua.source.output = smua.OUTPUT_ON 
    
    local results = {} 
    
    for mode = 1, 2 do -- 1 = pre-post, 2 = post-pre 
        for k = 1, total_dt do 
            local dt = dt_list[k] 
            print("-- Status: STDP mode " .. mode .. ", dt = " .. dt .. " s") 
            
            -- Reset to common baseline 
            for i = 1, 5 do 
                smua.source.levelv = -15 
                delay(0.1) 
                smua.source.levelv = 0 
                delay(0.1) 
            end 
            delay(1) 
            
            -- Initial weight, 5-read avg 
            smua.source.levelv = readV 
            delay(0.05) 
            local s = 0 
            for i = 1, 5 do 
                s = s + smua.measure.i() 
                delay(0.05) 
            end 
            local w_i = s / 5 
            smua.source.levelv = 0 
            delay(0.2) 
            
            -- STDP STIMULATION TRAIN
            if mode == 1 then 
                -- pulse pair, pure delays (Pre-Post)
                smua.source.levelv = writeV_Pos 
                delay(width) 
                smua.source.levelv = 0 
                delay(dt) 
                smua.source.levelv = writeV_Neg 
                delay(width) 
            else 
                -- pulse pair, pure delays (Post-Pre)
                smua.source.levelv = writeV_Neg 
                delay(width) 
                smua.source.levelv = 0 
                delay(dt) 
                smua.source.levelv = writeV_Pos 
                delay(width) 
            end 
            
            smua.source.levelv = 0 
            delay(0.5) 
            
            -- Final weight, 5-read avg 
            smua.source.levelv = readV 
            delay(0.05) 
            s = 0 
            for i = 1, 5 do 
                s = s + smua.measure.i() 
                delay(0.05) 
            end 
            local w_f = s / 5 
            smua.source.levelv = 0 
            
            -- ⚡ RUNTIME FIX: Replaced 'abs()' call with our custom safe function
            local dW = ((w_f - w_i) / absolute_value(w_i)) * 100 
            
            local dt_signed = dt 
            if mode == 2 then 
                dt_signed = -dt 
            end 
            
            -- Storing the data arrays safely using table lookup offsets
            local next_idx = table.getn(results) + 1
            results[next_idx] = {dt_signed, w_i, w_f, dW} 
            
            -- ⏱️ 3-MINUTE COOLDOWN GAP:
            -- Shuts down outputs and gives the device 180 seconds of rest 
            -- before moving on to the next dt parameter profile.
            smua.source.levelv = 0
            print("-- [LOOP] Point complete. Entering deep cooldown for 3 minutes...")
            delay(180.0)
        end 
    end 
    
    smua.source.output = smua.OUTPUT_OFF 
    
    -- PRINT FINAL SUMMARY DATA BLOCK
    print("") 
    print("dt(s)", "W_init(A)", "W_final(A)", "DeltaW(%)") 
    
    local total_results = table.getn(results)
    for i = 1, total_results do 
        local r = results[i] 
        print(string.format("%g\t%g\t%g\t%g", r[1], r[2], r[3], r[4])) 
    end 
    print("-- STDP curve complete.") 
end 

-- EXECUTE: 12 points total across both branches
run_STDP_Curve()
===================================================
SRDP
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
-- Measures: SRDP clean with per-pulse data
-- Fixed: Removed redundant post-test measurement artifacts
-- Fixed: Pulse 50 is now strictly treated as the final state for SRDP calculations

function run_SRDP(pulseWidth, pulseCount, frequency, postWait) 
    -- Execute hardware clear followed by absolute recovery window
    reset_device()
    delay(5.0) -- Safety buffer for physical device relaxation
    
    -- Locked hardware parameters
    local writeV = 15.0
    local readV = 1.0
    
    pulseWidth = pulseWidth or 0.02 
    pulseCount = pulseCount or 50 
    frequency = frequency or 2.0 
    postWait = postWait or 0.5 
    
    local readDelay = 0.05 -- Overhead duration for the measurement step
    local period = 1 / frequency 
    
    -- Maintain exact frequency by embedding read step inside the period
    local offGap = period - pulseWidth - readDelay
    
    -- Frequency safety checks
    if offGap <= 0 then 
        print(string.format("-- ERROR: At %g Hz, pulseWidth + read overhead exceeds total period!", frequency)) 
        return 
    end 
    if offGap < 0.005 then 
        print(string.format("-- ERROR: At %g Hz, remaining offGap is too small for SMU settling time.", frequency)) 
        return 
    end 
    
    smua.reset() 
    smua.source.func = smua.OUTPUT_DCVOLTS 
    smua.source.output = smua.OUTPUT_ON 
    smua.measure.autorangei = smua.AUTORANGE_OFF 
    smua.measure.rangei = 1e-4 
    smua.source.limiti = 1e-3 
    
    print("\n-- ==========================================")
    print("-- TEST: SRDP streamlined protocol") 
    print(string.format( "-- PARAMS: writeV=%g V readV=%g V pulseWidth=%g s frequency=%g Hz (Period=%g s) net_offGap=%g s", 
                        writeV, readV, pulseWidth, frequency, period, offGap )) 
    print("-- ==========================================")
    
    -- Establish initial baseline state (G0)
    smua.source.levelv = readV 
    delay(0.05)
    local I0 = smua.measure.i()
    local G0 = (I0 / readV) * 1e6 
    smua.source.levelv = 0
    print(string.format("-- BASELINE: I0=%g A G0=%g uS", I0, G0)) 
    
    print("Pulse#\tCurrent(A)\tConductance(uS)\tDeltaG(%)") 
    
    -- Variables to hold the final pulse state values
    local finalI = 0
    local finalG = 0
    
    for i = 1, pulseCount do 
        -- WRITE PULSE
        smua.source.levelv = writeV 
        delay(pulseWidth) 
        
        -- FIRST PART OF INTER-SPIKE INTERVAL
        smua.source.levelv = 0 
        delay(offGap) 
        
        -- SECOND PART OF INTER-SPIKE INTERVAL: NON-DESTRUCTIVE READ
        smua.source.levelv = readV 
        delay(readDelay) 
        local curr = smua.measure.i() 
        
        local G = (curr / readV) * 1e6 
        local dG = 0 
        if G0 ~= 0 then 
            dG = ((G - G0) / G0) * 100 
        end 
        
        print(string.format("%d\t%g\t%g\t%g", i, curr, G, dG)) 
        
        -- Dynamically capture the last pulse values
        if i == pulseCount then
            finalI = curr
            finalG = G
        end
    end 
    
    -- Post-test shutdown
    smua.source.levelv = 0 
    smua.source.output = smua.OUTPUT_OFF 
    delay(postWait) 
    
    -- Calculate SRDP index directly from the 50th pulse
    local idx = 0 
    if G0 ~= 0 then 
        idx = ((finalG - G0) / G0) * 100 
    end 
    
    print(string.format( "-- RESULT: frequency=%g Hz I0=%g A G0=%g uS I_final=%g A G_final=%g uS SRDP_index=%g %%", 
                        frequency, I0, G0, finalI, finalG, idx )) 
    print("-- END OF TEST RUN\n")
end 

-- ==================================================
-- AUTOMATED EXECUTION BLOCK
-- ==================================================

local frequencies = {2.0, 4.0, 6.0, 8.0, 10.0}
local totalTests = table.getn(frequencies)

print("-- Starting Automated Multi-Frequency SRDP Test Suite...")

for idx = 1, totalTests do
    local freq = frequencies[idx]
    print(string.format("-- [LOOP] Running automated test %d of %d...", idx, totalTests))
    
    run_SRDP(0.02, 50, freq, 0.5)
    
    print("-- [LOOP] Cooling down device before next automated sweep...")
    delay(5.0) 
end

print("-- ✅ All streamlined SRDP tests completed successfully!")
====================================================
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


run_Retention(60)
run_Retention(40)
run_Retention(20)

print("")
print("ALL RETENTION TESTS COMPLETED")
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
===============================================================
================================================================
posV = 18
negV = -15
readV = 1.5
pulseWidth = 0.1
gap = 0.05
nPulses = 100

smua.reset()
smua.source.func = smua.OUTPUT_DCVOLTS
smua.source.rangev = 20
smua.measure.autorangei = smua.AUTORANGE_OFF
smua.measure.rangei = 1e-6
smua.source.limiti = 1e-3
smua.measure.nplc = 1
smua.source.levelv = 0
smua.source.output = smua.OUTPUT_ON

print("Reset: 3 pulses at -15V")
for i = 1, 3 do
    smua.source.levelv = negV
    delay(pulseWidth)
    smua.source.levelv = 0
    delay(gap)
end
delay(1)

print("Pulse count sweep: +18V, target ~0.5 uS")
print("Pulse#\tG(uS)")

smua.source.levelv = readV
delay(0.3)
g = math.abs(smua.measure.i()/readV)*1e6
smua.source.levelv = 0
print(string.format("0\t%g", g))

for i = 1, nPulses do
    smua.source.levelv = posV
    delay(pulseWidth)
    smua.source.levelv = 0
    delay(gap)
    smua.source.levelv = readV
    delay(0.3)
    g = math.abs(smua.measure.i()/readV)*1e6
    smua.source.levelv = 0
    print(string.format("%d\t%g", i, g))
end

smua.source.levelv = 0
smua.source.output = smua.OUTPUT_OFF
print("Sweep done.")
==================================================
==================================================
