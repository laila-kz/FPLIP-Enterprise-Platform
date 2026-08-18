<?php

// Referenced by the findings-submission validation rule
// (Rule::in(config('investigations.root_cause_categories'))) instead of a
// DB enum, so this list can be edited and deployed without a migration.
return [
    'root_cause_categories' => [
        'Tooling Wear',
        'Changeover Delay',
        'Material Defect',
        'Machine Calibration',
        'Operator Error',
        'Sensor/Equipment Fault',
        'Dimensional Out-of-Spec',
        'Surface Finish Defect',
        'Unplanned Maintenance',
        'Other',
    ],

    // Max upload size in KB and allowed MIME types for evidence uploads —
    // referenced by both the request validation rule and the private
    // storage disk configuration.
    'evidence' => [
        'max_kilobytes' => 5120,
        'allowed_mimes' => ['jpg', 'jpeg', 'png'],
    ],
];
