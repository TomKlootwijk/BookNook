using UnityEngine;

/// <summary>
/// Spatiotemporal Bullet-Time and Shootdodge Controller
/// Designer: Tom Klootwijk (NL200678942 10-07-1990)
/// </summary>
public class BulletTimeController : MonoBehaviour
{
    [Header("Time Dilatation Config")]
    [Tooltip("Global time scale factor when bullet-time is active.")]
    [Range(0.05f, 0.5f)] public float bulletTimeScale = 0.20f;
    [Tooltip("Speed at which the engine interpolates into slow motion.")]
    public float enterTransitionSpeed = 5f;
    [Tooltip("Speed at which the engine restores normal time flow.")]
    public float exitTransitionSpeed = 5f;

    [Header("Resource Metric Management")]
    [Tooltip("Maximum bullet-time capacity in seconds.")]
    public float maxTimeResource = 10f;
    [Tooltip("Linear decay factor per real second during bullet-time.")]
    public float resourceDecayRate = 1.5f;
    [Tooltip("Resource points instantly gained per target neutralization.")]
    public float killRewardBonus = 2.0f;

    [Header("Shootdodge Kinematics")]
    [Tooltip("Horizontal forward/lateral velocity multiplier applied on dive.")]
    public float shootdodgeImpulseForce = 12f;
    [Tooltip("Vertical vertical lift height curve coefficient.")]
    public float shootdodgeJumpForce = 4.5f;

    // Internal State Trackers
    private float currentResource;
    private bool isBulletTimeActive = false;
    private bool isShootdodging = false;
    private Vector3 shootdodgeDirection;

    // Cached Component Reference
    private CharacterController characterController;
    private float targetTimeScale = 1.0f;
    private float normalFixedDeltaTime;

    private void Awake()
    {
        characterController = GetComponent<CharacterController>();
        normalFixedDeltaTime = Time.fixedDeltaTime;
        currentResource = maxTimeResource;
    }

    private void Update()
    {
        HandleInput();
        UpdateSpatiotemporalMatrix();
    }

    private void HandleInput()
    {
        // Toggle Bullet-Time via Standard Fire2 / Right Click
        if (Input.GetButtonDown("Fire2") && !isShootdodging)
        {
            if (currentResource > 0.5f)
            {
                SetBulletTimeState(!isBulletTimeActive);
            }
        }

        // Trigger Shootdodge via Combined Evade Command (e.g., Space + Movement Direction)
        if (Input.GetButtonDown("Jump") && !isShootdodging && isBulletTimeActive)
        {
            float horizontal = Input.GetAxisRaw("Horizontal");
            float vertical = Input.GetAxisRaw("Vertical");

            if (Mathf.Abs(horizontal) > 0.1f || Mathf.Abs(vertical) > 0.1f)
            {
                Vector3 moveDir = new Vector3(horizontal, 0f, vertical).normalized;
                shootdodgeDirection = transform.TransformDirection(moveDir);
                StartShootdodge();
            }
        }
    }

    private void UpdateSpatiotemporalMatrix()
    {
        // Linear Resource Depletion Check
        if (isBulletTimeActive && !isShootdodging)
        {
            currentResource -= resourceDecayRate * Time.unscaledDeltaTime;
            if (currentResource <= 0f)
            {
                currentResource = 0f;
                SetBulletTimeState(false);
            }
        }

        // Asymmetric Engine Time Scale Interpolation Loop (Fixed Delta Time Lockstep)
        float currentSpeed = isBulletTimeActive ? enterTransitionSpeed : exitTransitionSpeed;
        Time.timeScale = Mathf.Lerp(Time.timeScale, targetTimeScale, Time.unscaledDeltaTime * currentSpeed);
        Time.fixedDeltaTime = normalFixedDeltaTime * Time.timeScale;

        // Perform Active Shootdodge Motion Matrix Update
        if (isShootdodging)
        {
            ExecuteShootdodgeMotion();
        }
    }

    private void SetBulletTimeState(bool activate)
    {
        isBulletTimeActive = activate;
        targetTimeScale = activate ? bulletTimeScale : 1.0f;
    }

    private void StartShootdodge()
    {
        isShootdodging = true;
        // Inject baseline vertical dynamic impulse decoupled from scaled global physics time
        Vector3 initialVelocity = shootdodgeDirection * shootdodgeImpulseForce + Vector3.up * shootdodgeJumpForce;
        StartCoroutine(ShootdodgePhysicsRoutine(initialVelocity));
    }

    private System.Collections.Inumerator ShootdodgePhysicsRoutine(Vector3 initialVelocity)
    {
        Vector3 currentVelocity = initialVelocity;
        float gravity = Physics.gravity.y;

        // Enforce the execution loop until ground contact registry
        while (isShootdodging)
        {
            // Standard kinematic equation framework evaluated using unscaled DeltaTime window
            currentVelocity.y += gravity * Time.unscaledDeltaTime;
            
            CollisionFlags flags = characterController.Move(currentVelocity * Time.unscaledDeltaTime);
            
            // Register state terminal lock if lower boundary registers grounding
            if ((flags & CollisionFlags.Below) != 0 && currentVelocity.y < 0)
            {
                isShootdodging = false;
                // Graceful evaluation cleanup: exit Bullet-Time on dive landing completion
                SetBulletTimeState(false);
                yield break;
            }

            yield return null;
        }
    }

    private void ExecuteShootdodgeMotion()
    {
        // Isolated hook placeholder for handling character orientation alignment / custom rotation independent of simulation tick
    }

    /// <summary>
    /// Public interface trigger invoked when external agent triggers an execution reward frame.
    /// </summary>
    public void RegisterNeutralizationReward()
    {
        currentResource = Mathf.Min(maxTimeResource, currentResource + killRewardBonus);
    }

    public float GetCurrentResourceNormalized()
    {
        return currentResource / maxTimeResource;
    }
}
