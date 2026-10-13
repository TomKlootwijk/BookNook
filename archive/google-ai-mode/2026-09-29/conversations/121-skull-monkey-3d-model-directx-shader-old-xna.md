# skull monkey 3D model directx shader old xna

Captured: 2026-10-08T20:43:40.600Z

Source: https://www.google.com/search?q=skull+monkey+3D+model+directx+shader+old+xna&sca_esv=fe9e84a888596578&sxsrf=APpeQnsNB95cpZkVkSUu2ncxgyvmeeKFSg%3A1791480296853&udm=50&fbs=ABfTbFVyMZGZf1hfvX9uKjN_-G8c4u0nXx4bEIpwm1lnNH832a9BVCEiB2iPJNekNderQwJGZIG7YID1eBGNWasq2rzB4RlcW4X0t7W1CPEtyYhleqh7IweeyVNWqTX5RChTUyAbpXbq7u89js5MabYsqXiFvZmKBMsXfAuW8TkGSxc_xCmRTiPaYy5_JXUFseMdIxGXCId4&vsint=&aep=1&ntc=1&cs=0&sa=X&ved=2ahUKEwjl3dyV-KqXAxVE6wIHHbXuJLQQ2J8OegQIDBAD&biw=1707&bih=898&dpr=1.5&mstk=AUtExfAr83dUYUe2bne37HPHfVFMziFY_0qXOw6FP-ssrpBJDciLEzhGVpDqv2TGzuXWq2wY4ciwTvq1kIJpdoDlwlU59XQPS16ErnqLKEOTqAUCYNVK1_ZCsfYR8yTWTL-bO-AOoJhyXmuPWd2x05tjcgGTClcEdY5hIP2MV-odFxLnJYZzksRsyHSaIO89i4MXTQ4GjmgLZRtNFddXQgAAyUvEYNnDF71RPGhZ4sJ4LMNauC94SATCSLTl4EqtChI9q4t1nJ6J5Z9ICTBiLU2pcX7v-_UiSvjXYQ3_XpSu-cmZrJZo8q3sL2eScL4dieM8HCBV2bVTzzngzPsG5bDnoiqUeBFqMKUSYQ&csuir=1&mtid=BNLHavOHGama-d8PlZCi0Aw

## Prompt 1 — You

skull monkey 3D model directx shader old xna

## Response 1 — Google AI Mode

To render a **3D Skull Monkey model** using the old **Microsoft XNA Game Studio Framework** (targeting DirectX 9 and Shader Model 2.0/3.0), you need a proper **HLSL High-Level Shading Language Effect file (****`.fx`)**. 

![](../assets/b8198132047e1c5b1c0d.png)Reddit +2

Below is a complete legacy-compliant HLSL shader structure designed for XNA 4.0 / 3.1, incorporating basic ambient, diffuse lighting, and texturing mappings suitable for classic game assets. 

![](../assets/d5e380a5d0f0779a0aa8.png)Weebly.com +1

### 🛠️ Legacy XNA DirectX Shading Effect (`SkullMonkey.fx`)

hlsl

```
// --- CUSTOM XNA PARAMETERS ---
float4x4 World;
float4x4 View;
float4x4 Projection;

float3 LightDirection = float3(0.577, -0.577, -0.577);
float4 AmbientColor = float4(0.2, 0.2, 0.2, 1.0);
float4 DiffuseColor = float4(1.0, 1.0, 1.0, 1.0);

// Texture parameters
texture ModelTexture;
sampler TextureSampler = sampler_state
{
    Texture = <ModelTexture>;
    MipFilter = LINEAR;
    MinFilter = LINEAR;
    MagFilter = LINEAR;
    AddressU = WRAP;
    AddressV = WRAP;
};

// --- DATA STRUCTURES ---
struct VertexShaderInput
{
    float4 Position : POSITION0;
    float3 Normal   : NORMAL0;
    float2 TexCoord : TEXCOORD0; // Required in XNA to prevent pipeline mismatches
};

struct VertexShaderOutput
{
    float4 Position : POSITION0;
    float2 TexCoord : TEXCOORD0;
    float3 Normal   : TEXCOORD1;
};

// --- VERTEX SHADER ---
VertexShaderOutput VertexShaderFunction(VertexShaderInput input)
{
    VertexShaderOutput output;

    // Transform position to clip space
    float4 worldPosition = mul(input.Position, World);
    float4 viewPosition = mul(worldPosition, View);
    output.Position = mul(viewPosition, Projection);

    // Transform normals to world space
    output.Normal = mul(input.Normal, (float3x3)World);
    output.TexCoord = input.TexCoord;

    return output;
}

// --- PIXEL SHADER ---
float4 PixelShaderFunction(VertexShaderOutput input) : COLOR0
{
    // Normalize interpolated normal
    float3 normal = normalize(input.Normal);
    
    // Calculate diffuse light intensity (Lambertian)
    float diffuseLighting = max(0, dot(normal, -normalize(LightDirection)));
    
    // Sample the color from the monkey skull texture map
    float4 textureColor = tex2D(TextureSampler, input.TexCoord);
    
    // Combine lighting calculations
    float4 lightColor = AmbientColor + (DiffuseColor * diffuseLighting);
    
    return textureColor * lightColor;
}

// --- TECHNIQUE DECLARATION ---
technique TexturedLighting
{
    pass Pass1
    {
        // Target legacy Direct3D 9 profiles for XNA compatibility
        VertexShader = compile vs_2_0 VertexShaderFunction();
        PixelShader  = compile ps_2_0 PixelShaderFunction();
    }
}
```

Use code with caution.

### 💻 XNA / C# Runtime Rendering Setup

To pass parameters from your XNA game engine code to this custom shader during the standard model draw call sequence: 

![](../assets/e8faab0b8c3f8809db77.png)RB Whitaker's Wiki +1

csharp

```
protected override void Draw(GameTime gameTime)
{
    GraphicsDevice.Clear(Color.CornflowerBlue);

    // Calculate matrices
    Matrix worldMatrix = Matrix.CreateScale(1.0f) * Matrix.CreateTranslation(Vector3.Zero);

    foreach (ModelMesh mesh in skullMonkeyModel.Meshes)
    {
        foreach (Effect effect in mesh.Effects)
        {
            // Bind HLSL shader variables
            effect.CurrentTechnique = effect.Techniques["TexturedLighting"];
            effect.Parameters["World"].SetValue(worldMatrix);
            effect.Parameters["View"].SetValue(camera.ViewMatrix);
            effect.Parameters["Projection"].SetValue(camera.ProjectionMatrix);
            
            // Set custom lighting parameters if needed
            effect.Parameters["ModelTexture"].SetValue(skullMonkeyTexture);
        }
        mesh.Draw();
    }

    base.Draw(gameTime);
}
```

Use code with caution.

### ⚠️ Common Pitfalls to Avoid in Old XNA Pipeline

* **Missing UV Maps Exception**: XNA will crash or show a blank screen if your `VertexShaderInput` contains semantic bindings (`TEXCOORD0`) that are completely absent from the actual vertex declaration buffer of the imported model geometry. 

  ![](../assets/ddba388d62c1e1663f6d.png)Game Development Stack Exchange
* **MonoGame Upgrades**: If you plan to port this asset stack to modern wrappers like [MonoGame Community](https://community.monogame.net/) later on, note that you will need to recompile this code target from `vs_2_0` / `ps_2_0` profiles over to modern **DirectX 11 (`vs_4_0_level_9_1`)** standards. 

  ![](../assets/20444d3f5f36af8f4d55.png)Game Developer +1

Are you loading a specific model format (like **.fbx** or **.x** formats)? Let me know if you need help writing a custom **Content Pipeline Extension** to map textures automatically when loading the model asset.

### Source links

- [Reddit](https://www.reddit.com/r/monogame/comments/zz7f7d/looking_for_help_with_xna_shader_in_monogame/)
- [Weebly.com](https://xnameetingpoint.weebly.com/xna-tutorials.html)
- [RB Whitaker's Wiki](https://rbwhitaker.wikidot.com/old-xna-tutorials)
- [Game Development Stack Exchange](https://gamedev.stackexchange.com/questions/15431/how-to-properly-set-up-xna-shader)
- [MonoGame Community](https://community.monogame.net/)
- [Game Developer](https://www.gamedeveloper.com/programming/from-xna-to-monogame)
