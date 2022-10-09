//BUILDER------------------------------------------------------------------------------------------
using Business.DependencyResolvers.Microsoft;
using Microsoft.Extensions.FileProviders;
using SignalR.Hubs;

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.ConfigureKestrel(serverOptions => {
    serverOptions.Limits.MaxRequestBodySize = 209715200;
});

//Services
builder.Services.AddDependencies();
builder.Services.AddControllersWithViews();

//APP----------------------------------------------------------------------------------------------
var app = builder.Build();
app.UseStatusCodePagesWithReExecute("/Home/NotFound", "?code={0}");
app.UseStaticFiles();
app.UseStaticFiles(new StaticFileOptions() {
    FileProvider = new PhysicalFileProvider(System.IO.Path.Combine(Directory.GetCurrentDirectory(), "node_modules")),
    RequestPath = "/node_modules"
});

app.UseRouting();
app.UseEndpoints(endpoints => {
    endpoints.MapHub<MasterHub>("/MasterHub");
    endpoints.MapControllerRoute(
        name: "default",
        pattern: "{Controller}/{Action}/{id?}",
        defaults: new { Controller = "Home", Action = "Index" }
    );
});

app.Run();
