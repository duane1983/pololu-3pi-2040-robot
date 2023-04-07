# This demo shows how the 3pi+ can use its gyroscope to detect when it is being
# rotated, and use the motors to resist that rotation.
#
# In the "Choose edition" menu, use the A and C buttons to select what type of
# 3pi+ robot you have.
#
# Be careful to not move the robot during gyro calibration, while it says
# "Calibrating..." on the screen.
#
# After the gyro calibration is done, press button A to start the motors.
# If you try to turn the 3pi+, or put it on a surface that is turning, it will
# drive its motors to counteract the turning.  This demo only uses the Z axis
# of the gyro, so it is possible to pick up the 3pi+, rotate it about its X
# and Y axes, and then put it down facing in a new position.

from pololu_3pi_2040_robot import robot
from pololu_3pi_2040_robot.extras import editions
import time

motors = robot.Motors()
button_a = robot.ButtonA()
button_c = robot.ButtonC()
display = robot.Display()
yellow_led = robot.YellowLED()

display.fill(0)
display.text("Starting IMU...", 0, 0, 1)
display.show()
imu = robot.IMU()
imu.reset()
imu.enable_default()
imu_start = time.ticks_ms()

edition = editions.select()

if edition == "Standard":
    max_speed = 3000
    kp = 160
    kd = 4
elif edition == "Turtle":   # TODO: tune
    max_speed = 6000
    kp = 200
    kd = 0
elif edition == "Hyper":    # TODO: tune
    motors.flip_left(True)
    motors.flip_right(True)
    max_speed = 1500
    kp = 200
    kd = 0

display.fill(0)
display.text("Calibrating...", 0, 0, 1)
display.show()
# skip spurious readings at startup
while time.ticks_diff(time.ticks_ms(), imu_start) < 500: pass
calibration_start = time.ticks_ms()
stationary_gz = 0.0
reading_count = 0
while time.ticks_diff(time.ticks_ms(), calibration_start) < 3000:
    if imu.gyro.data_ready():
        imu.gyro.read()
        stationary_gz += imu.gyro.last_reading_dps[2]
        reading_count += 1
stationary_gz /= reading_count

drive_motors = False
last_time = None
turn_rate = 0
angle = 0.0
log = None
log_start_time = None

def log_time():
    return time.ticks_diff(time.ticks_us(), log_start_time)

def draw_text():
  display.fill(0)
  a = "A: Stop motors" if drive_motors else "A: Start motors"
  display.text(a, 0, 0, 1)
  display.text(f"Angle:", 0, 32, 1)
  if log: display.text("Logging", 0, 48, 1)
  display.text(edition, 0, 56, 1)

draw_text()

while True:
    # Update the angle and the turn rate.
    if imu.gyro.data_ready():
        imu.gyro.read()
        turn_rate = imu.gyro.last_reading_dps[2] - stationary_gz  # degrees per second
        now = time.ticks_us()
        if last_time:
            dt = time.ticks_diff(now, last_time)
            angle += turn_rate * dt / 1000000
        last_time = now
        if log: print(f"{log_time()},{angle:.3f}", file=log)

    # If the user presses button A, toggle whether the motors are on.
    if button_a.check() == True:
        drive_motors = not drive_motors
        if drive_motors:
            display.fill(1)
            display.text("Spinning", 30, 20, 0)
            display.text("WATCH OUT", 27, 30, 0)
            display.show()
            time.sleep_ms(500)
        draw_text()
        last_time = time.ticks_us()

    # If the user pressed button C, toggle data logging.
    if button_c.check() == True:
        if log:
            log.close()
            log = None
        else:
            log = open("rotation.log", "w")
            log_start_time = time.ticks_us()
        draw_text()

    # Show the current angle in degrees.
    display.fill_rect(48, 32, 72, 8, 0)
    display.text(f"{angle:>9.3f}", 48, 32, 1)
    display.show()

    # Drive motors.
    if drive_motors:
        speed = angle * kp + turn_rate * kd
        if speed > max_speed: speed = max_speed
        if speed < -max_speed: speed = -max_speed
        motors.set_speeds(speed, -speed)
        yellow_led.on()
    else:
        motors.off()
        yellow_led.off()
