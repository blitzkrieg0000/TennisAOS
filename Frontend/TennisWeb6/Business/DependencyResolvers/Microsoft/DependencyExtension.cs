using AutoMapper;
using Business.Interfaces;
using Business.Mappings.AutoMapper;
using Business.Services;
using Business.ValidationRules;
using DataAccess.Contexts;
using DataAccess.UnitOfWork;
using Dtos.PlayerDtos;
using Dtos.SessionDtos;
using Dtos.StreamDtos;
using Entities.Concrete.Security;
using FluentValidation;
using IdentityProjesi.CustomDescriber;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Http.Features;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace Business.DependencyResolvers.Microsoft {
    public static class DependencyExtension {

        public static void AddDependencies(this IServiceCollection services) {
            services.Configure<FormOptions>(x => {
                x.MultipartBodyLengthLimit = 209715200;
            });

            //! SERVICE SETTINGS
            services.AddSignalR(options => options.MaximumParallelInvocationsPerClient = 10);

            services.AddIdentity<AppUser, AppRole>(opt => {
                opt.Password.RequireDigit = false;
                opt.Password.RequiredLength = 1;
                opt.Password.RequireLowercase = false;
                opt.Password.RequireUppercase = false;
                opt.Password.RequireNonAlphanumeric = false;
                opt.SignIn.RequireConfirmedEmail = false;
                opt.Lockout.MaxFailedAccessAttempts = 10;
            }).AddErrorDescriber<CustomErrorDescriber>().AddEntityFrameworkStores<SecurityContext>();

            services.ConfigureApplicationCookie(opt => {
                opt.Cookie.HttpOnly = true;
                opt.Cookie.SameSite = SameSiteMode.Strict;
                opt.Cookie.SecurePolicy = CookieSecurePolicy.SameAsRequest;
                opt.Cookie.Name = "TennisCookie";
                opt.ExpireTimeSpan = TimeSpan.FromDays(7);
                opt.LoginPath = new PathString("/Home/Index");
                opt.AccessDeniedPath = new PathString("/Home/AccessDenied");
            });

            services.AddControllersWithViews();


            //! DEPENDENCY INJECTIONS
            //Context in OnConfiguring kısmını dependency injection aracılığıyla yapıyoruz.
            // services.AddDbContext<TennisContext>(opt => {
            //     opt.UseNpgsql("Host=localhost;Database=tenis;Username=tenis;Password=2sfcNavA89A294V4;Pooling=false;Timeout=300;CommandTimeout=300", builder => {
            //         builder.EnableRetryOnFailure(3, TimeSpan.FromSeconds(10), null);
            //     });
            //     opt.LogTo(Console.WriteLine, LogLevel.Information);
            // });

            services.AddDbContext<SecurityContext>(opt => {
                opt.UseNpgsql("Host=postgres;Database=tenis;Username=tenis;Password=2sfcNavA89A294V4;Pooling=false;Timeout=300;CommandTimeout=300", builder => {
                    builder.EnableRetryOnFailure(3, TimeSpan.FromSeconds(10), null);
                });
                opt.LogTo(Console.WriteLine, LogLevel.Information);
            });

            services.AddScoped<IUnitOfWork, UnitOfWork>();
            services.AddScoped<IPlayingDatumService, PlayingDatumService>();
            services.AddScoped<IStreamService, StreamService>();
            services.AddScoped<IGRPCService, GRPCService>();
            services.AddScoped<IPlayerService, PlayerService>();
            services.AddScoped<IAosTypeService, AosTypeService>();
            services.AddScoped<ICourtService, CourtService>();
            services.AddScoped<ICourtTypeService, CourtTypeService>();
            services.AddScoped<ISessionService, SessionService>();
            services.AddScoped<IGenericService, GenericService>();
            services.AddScoped<IProcessService, ProcessService>();
            services.AddScoped<IProcessParameterService, ProcessParameterService>();
            services.AddScoped<IProcessResponseService, ProcessResponseService>();
            services.AddScoped<ITennisService, TennisService>();


            //Validators
            services.AddTransient<IValidator<StreamCreateDto>, StreamCreateDtoValidator>();
            services.AddTransient<IValidator<PlayerCreateDto>, PlayerCreateDtoValidator>();
            services.AddTransient<IValidator<SessionCreateDto>, SessionCreateDtoValidator>();


            //! AUTOMAPPER CONFIGURATIONS
            var configuration = new MapperConfiguration(opt => {
                opt.AddProfile(new TennisProfile());
            });
            var mapper = configuration.CreateMapper();
            services.AddSingleton(mapper);

            //! GRPC
            services.AddGrpc();
        }

    }
}